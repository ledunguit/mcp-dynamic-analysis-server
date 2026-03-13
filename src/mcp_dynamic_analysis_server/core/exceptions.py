class DynamicAnalysisError(Exception):
    """Base error for dynamic analysis server."""


class ValidationError(DynamicAnalysisError):
    """Input validation failed."""


class RunnerError(DynamicAnalysisError):
    """Execution failed."""


class ArtifactNotFound(DynamicAnalysisError):
    """Artifact not found."""
