use std::io;
use std::fmt;
use std::error::Error;

#[derive(Debug)]
pub enum CqcError {
    General,
    Io(io::Error),
    NoQubit,
    Unsupported,
    Timeout,
}

impl Error for CqcError {
    fn description(&self) -> &str {
        match self {
            &CqcError::General => "General error",
            &CqcError::Io(ref io_err) => io_err.description(),
            &CqcError::NoQubit => "No qubit with the specified ID for this application",
            &CqcError::Unsupported => "Command not supported by implementation",
            &CqcError::Timeout => "Timeout",
        }
    }
}

impl fmt::Display for CqcError {
    fn fmt(&self, f: &mut fmt::Formatter) -> Result<(), fmt::Error> {
        match self {
            &CqcError::Io(ref io_err) => io_err.fmt(f),
            _ => write!(f, "{}", self.description()),
        }
    }
}

impl From<io::Error> for CqcError {
    fn from(error: io::Error) -> Self {
        CqcError::Io(error)
    }
}
