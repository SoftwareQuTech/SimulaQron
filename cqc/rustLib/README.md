
This is a sample integration of the Rust library for accessing the CQC backend.  This integration uses the CQC crate which can be found on [crates.io](https://crates.io/crates/cqc).

To build the library (do not forget to include `--release` for an optimised build)

```console
cargo build
```

To run tests

```console
./tests/run_test.sh
```

It is recommended to run the tests in the Docker container which is set up with the rust toolchain and the necessary runtime environment for SimulaQron.  The Dockerfile is available in the root of the repository.

To build the docker container and run the tests:

1. Make sure [docker is installed](https://docs.docker.com/install/).

2. Go to root of the SimulaQron directory and run

```console
docker build -t simulaqron .
```

3. Once the build finishes launch the container with

```console
docker run -it -v $(pwd):/workspace/SimulaQron simulaqron
```

4. Inside the container change directory into `cqc/rustLib`

5. And now you can run tests with

```console
./tests/run_test.sh
```
