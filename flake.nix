{
  description = "Kubectl overlay for Nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.05";
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
    };
}
