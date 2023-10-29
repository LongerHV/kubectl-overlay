{
  description = "Kubectl overlay for Nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      forAllSystems = nixpkgs.lib.genAttrs [ "aarch64-linux" "x86_64-linux" ];
      overlay = import ./overlay.nix;
    in
    {
      overlays.default = overlay;
      legacyPackages = forAllSystems (system:
        import nixpkgs {
          inherit system;
          overlays = [ overlay ];
        }
      );
      devShells = forAllSystems (system:
        let pkgs = nixpkgs.legacyPackages.${system}; in {
          update = pkgs.mkShellNoCC {
            buildInputs = with pkgs.python3Packages; [ python requests packaging dacite ];
          };
        });
    };
}
