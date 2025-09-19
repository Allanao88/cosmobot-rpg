{ pkgs }: {
  deps = [
    pkgs.python3
    pkgs.python3Packages.pip
    pkgs.python3Packages.discordpy
    pkgs.python3Packages.python-dotenv
    pkgs.python3Packages.flask
  ];
}