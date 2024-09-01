# Kubectl overlay

Nix overlay containing derivations for 5 latest minor releases of [kubectl](https://kubernetes.io/docs/reference/kubectl/).
The overlay is updated daily using a GHA workflow.

## Usage

### Nix run

You can use `nix run` to invoke kubectl without installation.

```bash
nix run github:LongerHV/kubectl-overlay#kubectl_latest -- get nodes
nix run github:LongerHV/kubectl-overlay#kubectl_1_31 -- get nodes
```

### Overlay (flakes)

Overlay can be added to NixOS or Home Manager configuration.

```nix
{
    inputs = {
        nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
        home-manager = {
            url = "github:nix-community/home-manager";
            inputs.nixpkgs.follows = "nixpkgs";
        };
        kubectl = {
            url = "github:LongerHV/kubectl-overlay";
            inputs.nixpkgs.follows = "nixpkgs";
        };
    };
    outputs = { nixpkgs, home-manager, kubectl, ... }: {
        # NixOS setup
        nixosConfigurations.my-workstation = nixpkgs.lib.nixosSystem {
            modules = [
                ./path/to/your/configuration.nix
                ({ pkgs, ... }: {
                    nixpkgs.overlays = [ kubectl.overlays.default ];
                    environment.systemPackages = [ pkgs.kubectl_latest ];
                })
            ];
        };
        # Standalone Home Manager setup
        homeConfigurations.my-home = home-manager.lib.homeManagerConfiguration {
            pkgs = nixpkgs.legacyPackages.x86_64-linux;
            modules = [
                ./path/to/your/home.nix
                ({ pkgs, ... }: {
                    nixpkgs.overlays = [ kubectl.overlays.default ];
                    home.packages = [ pkgs.kubectl_latest ];
                })
            ];
        };
    };
}
```
