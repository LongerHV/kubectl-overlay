version: hash:
{ lib
, buildGoModule
, fetchFromGitHub
, runtimeShell
, installShellFiles
, rsync
, ...
}:

buildGoModule {
  pname = "kubectl";
  inherit version;

  src = fetchFromGitHub {
    owner = "kubernetes";
    repo = "kubernetes";
    rev = "v${version}";
    inherit hash;
  };

  vendorHash = null;

  doCheck = false;

  nativeBuildInputs = [ installShellFiles rsync ];

  outputs = [ "out" "man" "convert" ];

  WHAT = lib.concatStringsSep " " [
    "cmd/kubectl"
    "cmd/kubectl-convert"
  ];

  buildPhase = ''
    runHook preBuild
    substituteInPlace "hack/update-generated-docs.sh" --replace "make" "make SHELL=${runtimeShell}"
    patchShebangs ./hack ./cluster/addons/addon-manager
    make "SHELL=${runtimeShell}" "WHAT=$WHAT"
    ./hack/update-generated-docs.sh
    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall
    install -D _output/local/go/bin/kubectl -t $out/bin
    install -D _output/local/go/bin/kubectl-convert -t $convert/bin

    installManPage docs/man/man1/kubectl*

    installShellCompletion --cmd kubectl \
      --bash <($out/bin/kubectl completion bash) \
      --fish <($out/bin/kubectl completion fish) \
      --zsh <($out/bin/kubectl completion zsh)
    runHook postInstall
  '';
}
