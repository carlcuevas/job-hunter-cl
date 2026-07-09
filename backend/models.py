from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    NEW = "nueva"
    SAVED = "guardada"
    APPLIED = "postulada"
    DISCARDED = "descartada"


class ApplicationStatus(str, Enum):
    SENT = "enviada"
    IN_REVIEW = "en_revision"
    INTERVIEW = "entrevista"
    REJECTED = "rechazada"
    OFFER = "oferta"


class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    modality: Optional[str] = None
    salary: Optional[str] = None
    description: str
    url: str
    source: str  # "laborum" | "getonboard" | "indeed"
    posted_at: Optional[str] = None
    scraped_at: datetime
    match_score: int = 0          # 0-100
    match_tags: List[str] = []    # keywords que matchearon
    status: JobStatus = JobStatus.NEW
    cover_letter: Optional[str] = None


class JobFilter(BaseModel):
    keyword: Optional[str] = None
    source: Optional[str] = None
    min_score: Optional[int] = 0
    status: Optional[JobStatus] = None
    modality: Optional[str] = None


class Application(BaseModel):
    id: str
    job_id: str
    job_title: str
    company: str
    source: str
    url: str
    applied_at: datetime
    status: ApplicationStatus = ApplicationStatus.SENT
    cover_letter: str
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = None


class ScrapeRequest(BaseModel):
    portals: List[str] = ["laborum", "getonboard"]
    keywords: Optional[List[str]] = None
    limit: int = 50
