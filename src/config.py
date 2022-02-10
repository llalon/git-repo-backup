class GitProvider(Enum):
    gitlab = auto()
    github = auto()

@dataclass
class Config:
    token: str
    owners: list[str]
    directory: Path
    method: GitProvider
    repos: list[str]
    host: str