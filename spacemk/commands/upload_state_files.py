import click


@click.command(help="Upload Terraform state files to state backend.")
@click.pass_context
def upload_state_files(ctx):
    console = ctx.obj["console"]

    console.print("This command has not been implemented yet.")
