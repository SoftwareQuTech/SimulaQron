CQC Rust Library
================

The Rust library is different from the C and Python libraries in that it is not part of the main SimulaQron repository. Instead it is hosted as a `Rust crate on crates.io <https://crates.io/crates/cqc>`_ in order to leverage the benefits of the Rust ecosystem. This includes automatically generated documentation and easy inclusion in Rust projects from a `Cargo.toml` file.

The CQC Rust crate is also different from the other libraries in that it is sans-io, that is, it does not handle the sending or receiving of packets. It only provides functionality for building, manipulating, encoding, and decoding packets. You can read more about the advantages of this design `here <https://sans-io.readthedocs.io/>`_. Whilst it was written with the Python ecosystem in mind the principles are more general.

You can find out more about the Rust crate at its
- `crates.io page <https://crates.io/crates/cqc>`_
- `GitHub repository <https://github.com/Wojtek242/cqc>`_
- `Documentation with examples <https://docs.rs/cqc>`_

The `crate's own documentation page <https://docs.rs/cqc>`_ will always have the most up-to-date documentation about the library so please use that as a reference when integrating with your Rust code.

There is a sample integration of the CQC crate provided in `cqc/rustLib` which implements a simple, synchronous mechanism for sending and receiving CQC packets. However, there is a risk that `cqc/rustLib` may be out of sync compared to the CQC crate itself. Please check `cqc/rustLib/Cargo.toml` which version it was based on. For the most up-to-date documentation, please refer to the `crate docs <https://docs.rs/cqc>`_.
