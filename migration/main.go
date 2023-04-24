package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"text/template"
	"time"

	git "github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/plumbing/object"
	"github.com/go-git/go-git/v5/plumbing/transport/http"
	"github.com/google/go-github/v38/github"
	"github.com/ktrysmt/go-bitbucket"
	"github.com/microsoft/azure-devops-go-api/azuredevops"
	azdo "github.com/microsoft/azure-devops-go-api/azuredevops/git"
	gitlab "github.com/xanzy/go-gitlab"
	"golang.org/x/oauth2"
	"gopkg.in/yaml.v3"
)

const (
	Red   = "\033[31m"
	Green = "\033[32m"
	Reset = "\033[0m"
)

func Colorize(text string, color string) string {
	return fmt.Sprintf("%s%s%s", color, text, Reset)
}

func RunTerraformCommand(command string) {
	var cmd *exec.Cmd
	if command == "apply" || command == "destroy" {
		cmd = exec.Command("terraform", command, "-auto-approve")
	} else if command == "loginS" {
		cmd = exec.Command("terraform", "login", "spacelift.io")
	} else if command == "apply_gen" {
		cmd = exec.Command("terraform", "apply", "-auto-approve", "-var-file=../out/data.json")
	} else {
		cmd = exec.Command("terraform", command)
	}

	if command == "login" || command == "loginS" {
		cmd.Stdin = os.Stdin
	}

	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	err := cmd.Run()
	if err != nil {
		fmt.Printf(Colorize("Error encountered while running 'terraform %s':\n", Red), command)
		os.Exit(1)
	}
	fmt.Printf(Colorize("terraform %s ran successfully\n\n", Green), command)
}

type TFC struct {
	Tfc_organization   string
	Export_state       bool
	Vcs_provider       string
	Vcs_namespace      string
	Vcs_default_branch string
}

type Spacelift struct {
	Stack_name                 string
	Stack_description          string
	Repository                 string
	Branch                     string
	Project_root               string
	Import_state               bool
	Spacelift_api_key_endpoint string
	VCS_provider               string
	VCS_namespace              string
}

type Config struct {
	Migration struct {
		Tfc_organization   string `yaml:"tfc_organization"`
		Vcs_provider       string `yaml:"vcs_provider"`
		Vcs_namespace      string `yaml:"vcs_namespace"`
		Spacelift_account  string `yaml:"spacelift_account"`
		Repo_name          string `yaml:"repo_name"`
		Vcs_default_branch string `yaml:"vcs_default_branch"`
	} `yaml:"migration_data"`
}

func set_default_tfc(tfc_organization, vcs_provider, vcs_namespace, vcs_default_branch string) TFC {
	tfc_config := TFC{
		Tfc_organization:   tfc_organization,
		Export_state:       true,
		Vcs_provider:       vcs_provider,
		Vcs_namespace:      vcs_namespace,
		Vcs_default_branch: vcs_default_branch,
	}
	return tfc_config
}

func set_default_spacelift(spacelift_organization, spacelift_repository, vcs_provider, vcs_namespace, vcs_default_branch string) Spacelift {
	spacelift_config := Spacelift{
		Stack_name:                 "Migration Manager",
		Stack_description:          "Manager Stack used for migration",
		Repository:                 spacelift_repository,
		Branch:                     vcs_default_branch,
		Project_root:               "",
		Import_state:               true,
		Spacelift_api_key_endpoint: fmt.Sprintf("https://%s.app.spacelift.io", spacelift_organization),
		VCS_provider:               vcs_provider,
		VCS_namespace:              vcs_namespace,
	}
	return spacelift_config
}

func tfc_template(tfc_tfvars_file, tfc_organization, vcs_provider, vcs_namespace, vcs_default_branch string) {
	tmpl, err := template.ParseFiles(tfc_tfvars_file)
	if err != nil {
		fmt.Println("Error:", err)
		return
	}

	tfc_config := set_default_tfc(tfc_organization, vcs_provider, vcs_namespace, vcs_default_branch)
	tf_vars, err := os.Create("../exporters/tfc/terraform.tfvars")
	if err != nil {
		fmt.Println("Error:", err)
		return
	}
	defer tf_vars.Close()

	err = tmpl.Execute(tf_vars, tfc_config)
	if err != nil {
		fmt.Println("Error:", err)
		return
	}
}

func spacelift_template(spacelift_tfvars_file, spacelift_organization, spacelift_repository, vcs_provider, vcs_namespace, vcs_default_branch string) {
	tmpl, err := template.ParseFiles(spacelift_tfvars_file)
	if err != nil {
		fmt.Println("Error:", err)
		return
	}

	spacelift_config := set_default_spacelift(spacelift_organization, spacelift_repository, vcs_provider, vcs_namespace, vcs_default_branch)
	tf_vars, err := os.Create("../manager-stack/terraform.tfvars")
	if err != nil {
		fmt.Println("Error:", err)
		return
	}
	defer tf_vars.Close()
	err = tmpl.Execute(tf_vars, spacelift_config)
	if err != nil {
		fmt.Println("Error:", err)
		return
	}
}

func cleanup() error {
	cmd := exec.Command("sh", "-c", "rm -rf ../out ../{exporters/tfc,generator,manager-stack}/.terraform ../{exporters/tfc,generator,manager-stack}/.terraform.lock.hcl ../{exporters/tfc,generator,manager-stack}/terraform.tfstate ../{exporters/tfc,generator,manager-stack}/terraform.tfstate.backup ../{exporters/tfc,generator,manager-stack}/terraform.tfvars")

	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	err := cmd.Run()

	return err
}

func createGithubRepo(token, repoName, repoDescription string, privateRepo bool) (string, error) {
	ctx := context.Background()
	ts := oauth2.StaticTokenSource(
		&oauth2.Token{AccessToken: token},
	)
	tc := oauth2.NewClient(ctx, ts)

	client := github.NewClient(tc)

	repo := &github.Repository{
		Name:        github.String(repoName),
		Description: github.String(repoDescription),
		Private:     github.Bool(privateRepo),
		AutoInit:    github.Bool(true),
	}

	createdRepo, _, err := client.Repositories.Create(ctx, "", repo)
	if err != nil {
		return "", err
	}

	httpURL := ""
	if createdRepo.CloneURL != nil {
		httpURL = *createdRepo.CloneURL
	}

	return httpURL, nil
}

func createGitlabRepo(token, repoName, repoDescription string, privateRepo bool) (string, error) {
	client, err := gitlab.NewClient(token)
	if err != nil {
		return "", err
	}

	visibility := gitlab.PublicVisibility
	if privateRepo {
		visibility = gitlab.PrivateVisibility
	}

	options := &gitlab.CreateProjectOptions{
		Name:        gitlab.String(repoName),
		Description: gitlab.String(repoDescription),
		Visibility:  &visibility,
	}

	project, _, err := client.Projects.CreateProject(options)
	if err != nil {
		return "", err
	}

	return project.HTTPURLToRepo, nil
}

func createAzureDevOpsRepo(token, project, repoName, organization string) (string, error) {
	ctx := context.Background()
	connection := azuredevops.NewPatConnection(fmt.Sprintf("https://dev.azure.com/%s", organization), token)

	client, err := azdo.NewClient(ctx, connection)
	if err != nil {
		return "", err
	}

	repo := azdo.GitRepositoryCreateOptions{
		Name: &repoName,
	}

	createdRepo, err := client.CreateRepository(ctx, azdo.CreateRepositoryArgs{
		Project:               &project,
		GitRepositoryToCreate: &repo,
	})
	if err != nil {
		return "", err
	}

	return *createdRepo.RemoteUrl, nil
}

func createBitbucketRepo(username, appPassword, workspace, repoName, repoDescription string, privateRepo bool) (string, error) {
	c := bitbucket.NewBasicAuth(username, appPassword)

	options := &bitbucket.RepositoryOptions{
		Owner:       workspace,
		RepoSlug:    repoName,
		Scm:         "git",
		IsPrivate:   fmt.Sprintf("%t", privateRepo),
		Description: repoDescription,
	}

	createdRepo, err := c.Repositories.Repository.Create(options)
	if err != nil {
		return "", err
	}

	cloneURL := ""
	if cloneLinks, ok := createdRepo.Links["clone"]; ok {
		links := cloneLinks.([]interface{})
		for _, link := range links {
			linkMap := link.(map[string]interface{})
			if linkMap["name"].(string) == "https" {
				cloneURL = linkMap["href"].(string)
				break
			}
		}
	}

	if cloneURL == "" {
		return "", fmt.Errorf("failed to find HTTPS clone URL for the created Bitbucket repository")
	}

	return cloneURL, nil
}

func CreateRepo(vcs_provider, token, repo_name, description, username, organization, workspace string) (string, error) {
	var repo_url string
	var err error
	switch vcs_provider {

	case "github", "github_enterprise":
		repo_url, err = createGithubRepo(token, repo_name, "This repository contains tfc migrated repositories", false)
		if err != nil {
			fmt.Println(err)
		}
	case "gitlab":
		repo_url, err = createGitlabRepo(token, repo_name, "This repository contains tfc migrated repositories", false)
		if err != nil {
			fmt.Println(err)
		}
	case "azure_devops":
		repo_url, err = createAzureDevOpsRepo(token, workspace, repo_name, organization)
		if err != nil {
			fmt.Println(err)
		}
	case "bitbucket":
		repo_url, err = createBitbucketRepo(username, token, workspace, repo_name, "This repository contains tfc migrated repositories", false)
		if err != nil {
			fmt.Println(err)
		}

	default:
		return "", fmt.Errorf("you have not provided a supported vcs provider: %s", vcs_provider)
	}

	if err != nil {
		return "", err
	}

	return repo_url, err
}

func cloneRepo(url, directory, token string) error {
	auth := &http.BasicAuth{
		Username: "your-username",
		Password: token,
	}

	// Clone the repository using the HTTP authentication
	_, err := git.PlainClone(directory, false, &git.CloneOptions{
		URL:  url,
		Auth: auth,
	})
	return err
}

func addCommitAndPush(directory, username, message, token string) error {
	r, err := git.PlainOpen(directory)
	if err != nil {
		return err
	}

	w, err := r.Worktree()
	if err != nil {
		return err
	}

	_, err = w.Add(".")
	if err != nil {
		return err
	}

	commit, err := w.Commit(message, &git.CommitOptions{
		Author: &object.Signature{
			Name: username,
			When: time.Now(),
		},
	})
	if err != nil {
		return err
	}

	obj, err := r.CommitObject(commit)
	if err != nil {
		return err
	}
	fmt.Println(obj)

	auth := &http.BasicAuth{
		Username: username,
		Password: token,
	}

	err = r.Push(&git.PushOptions{
		Auth: auth,
	})
	if err != nil {
		return err
	}

	return nil
}

func copyFile(src, dst string) error {
	srcFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer srcFile.Close()

	dstFile, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer dstFile.Close()

	_, err = io.Copy(dstFile, srcFile)
	if err != nil {
		return err
	}

	err = dstFile.Sync()
	if err != nil {
		return err
	}

	return nil
}

func main() {

	login := flag.Bool("login", false, "Whether or not for script to run the terraform login commands. If you omit this version you must ensure you have logged it to both TFC and Spacelift")
	clean := flag.Bool("c", false, "Use this to start a new migration")
	help := flag.Bool("h", false, "Displays help")
	migrate := flag.Bool("migrate", false, "Whether or not to start a migration")

	flag.Parse()

	if *clean {
		cleanup()
		os.Exit(0)
	}

	if *help {
		flag.Usage()
		os.Exit(0)
	}

	if *login {
		RunTerraformCommand("loginS")
		RunTerraformCommand("login")
	}

	if *migrate {
		fmt.Print("A migration will start, and this assumes you have configured the config.yaml file and set the following environment variables TF_VAR_spacelift_api_key_id, TF_VAR_spacelift_api_key_secret and VCS_Token.\nPress y or yes to continue: ")

		var input string
		_, err := fmt.Scanln(&input)
		if err != nil {
			fmt.Println("Error reading input:", err)
			return
		}

		if input != "yes" && input != "y" {
			os.Exit(1)
		}

		data, err := ioutil.ReadFile("config.yaml")
		if err != nil {
			log.Fatalf("Error reading config.yaml: %v", err)
		}

		// Unmarshal the YAML data into a Config struct
		var config Config
		err = yaml.Unmarshal(data, &config)
		if err != nil {
			log.Fatalf("Error unmarshaling YAML data: %v", err)
		}

		tfc_template("exporter-tfvars.tpl", config.Migration.Tfc_organization, config.Migration.Vcs_provider, config.Migration.Vcs_namespace, config.Migration.Vcs_default_branch)
		os.Chdir("../exporters/tfc")
		RunTerraformCommand("init")
		RunTerraformCommand("apply")

		os.Chdir("../../generator")
		RunTerraformCommand("init")
		RunTerraformCommand("apply_gen")
		os.Chdir("../migration")

		token := os.Getenv("VCS_TOKEN")
		repo_url, err := createGithubRepo(token, config.Migration.Repo_name, "This repository contains tfc migrated repositories", false)
		if err != nil {
			fmt.Println(err)
		}

		err = cloneRepo(repo_url, "../../tfc_migration", token)
		if err != nil {
			fmt.Printf("Error: %v\n", err)
			return
		}
		copyFile("../out/main.tf", "../../tfc_migration/main.tf")
		addCommitAndPush("../../tfc_migration", "this", "initial commit for the tfc_migration", token)

		spacelift_template("manager-tfvars.tpl", config.Migration.Spacelift_account, config.Migration.Repo_name, config.Migration.Vcs_provider, config.Migration.Vcs_namespace, config.Migration.Vcs_default_branch)
		os.Chdir("../manager-stack")
		RunTerraformCommand("init")
		RunTerraformCommand("apply")
	}
}
