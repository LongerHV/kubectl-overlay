final: prev:
let
  versions = prev.lib.importJSON ./versions.json;
  buildKubectl = name: args: prev.callPackage (import ./kubectl.nix args.version args.hash) { };
in
builtins.mapAttrs buildKubectl versions
