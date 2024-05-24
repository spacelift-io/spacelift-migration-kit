# smk-docker

```shell
DOCKER_BUILDKIT=1 docker image build --file=data/smk-docker/Dockerfile --platform linux/amd64 --progress=plain --tag jmfontaine/smk-dark-warrior:2 .

docker run -it --rm --env GH_API_TOKEN --env TF_API_TOKEN --volume $PWD/config.yml:/app/config.yml --volume $PWD/tmp-docker:/app/tmp --volume /var/run/docker.sock:/var/run/docker.sock jmfontaine/smk-dark-warrior:2 <COMMAND>
```