import click
import sys
import cmd
from process_monitor import ProcessMonitor
from zap import Zapper
from term_sesh import TermSesh

class ZapShell(cmd.Cmd):
    intro = 'Welcome to the Zap CLI. Type help or ? to list commands.\n'
    prompt = 'zap> '

    def __init__(self):
        super().__init__()
        self.ctx = None
        self.zapper = None
        self.term_sesh = None

    # Command definitions
    def do_hello(self, arg):
        """Say hello"""
        click.echo('Hello!')

    def do_echo(self, arg):
        """Echo the input"""
        click.echo(arg)

    def do_exit(self, arg):
        """Exit the application"""
        click.echo('Goodbye!')
        if self.term_sesh:
            if self.term_sesh.monitor:
                self.term_sesh.monitor.is_running = False
            if self.term_sesh.terminal_process:
                self.term_sesh.terminal_process.terminate()
            self.term_sesh.kill_tmux_session()
        click.echo('Goodbye!')
        return True
        return True

    def do_start(self, arg):
        """Start up the terminal session using tmux"""
        self.zapper = Zapper()
        self.zapper.start()
        self.term_sesh = TermSesh(session_name='zapper_session')
        if self.term_sesh.open_new_terminal():
            self.term_sesh.monitor = ProcessMonitor(self.term_sesh)
            self.term_sesh.monitor.start_monitoring()
            click.echo("tmux session and monitoring started successfully")
            self.term_sesh.publisher.send_json({'type': 'info', 'data': 'tmux session started'})
            self.term_sesh.send_to_terminal("ls")
            self.term_sesh.send_to_terminal("cat setup.py")
        else:
            click.echo("Failed to start terminal session")



    def do_send(self, arg):
        """Send a command to the terminal"""
        if not self.term_sesh or not self.term_sesh.is_terminal_active():
            click.echo("No active terminal session. Use 'start' first.")
            return

        response = self.term_sesh.send_to_terminal(arg)
        if response:
            click.echo(f"Command sent: {response}")
    def do_quit(self, arg):
        """Exit the application"""
        return self.do_exit(arg)

    # Shortcut for exit
    do_EOF = do_quit

    def default(self, line):
        """Handle unknown commands"""
        if self.term_sesh and self.term_sesh.is_terminal_active():
            self.do_send(line)
        else:
            click.echo(f"Unknown command: {line}")
        click.echo(f"Unknown command: {line}")
    def precmd(self, line):
            """Check terminal status before each command"""
            if self.term_sesh and not self.term_sesh.is_terminal_active():
                click.echo("Terminal session ended unexpectedly")
            return line

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Zap CLI - An interactive command line tool"""
    if ctx.invoked_subcommand is None:
        # Start the interactive shell
        shell = ZapShell()
        shell.ctx = ctx
        shell.cmdloop()

@cli.command()
def version():
    """Show the version"""
    click.echo('Zap CLI v0.1.0')

def main():
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nGoodbye!")
        sys.exit(0)

if __name__ == '__main__':
    main()
