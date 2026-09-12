from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class BoundingRect(BaseModel):
    x: float
    y: float
    width: float
    height: float

class DOMNodeDescriptor(BaseModel):
    nodeId: str
    tagName: str
    role: Optional[str] = None
    text: Optional[str] = None
    placeholder: Optional[str] = None
    inputType: Optional[str] = None
    nameAttr: Optional[str] = None
    idAttr: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)
    bounds: BoundingRect
    isInput: bool
    isClickable: bool
    isVisible: bool
    sanitizedValue: Optional[str] = None
    appliedTreatment: Optional[str] = None
    assignedToken: Optional[str] = None

class PrivacyBoundaryReport(BaseModel):
    timestamp: int
    rawEntitiesDetected: int
    entitiesTransmitted: int
    entitiesBlocked: int
    entitiesTokenized: int
    localOnlyEntities: int
    sanitizedPayloadSizeBytes: int
    rawPayloadSizeBytes: int
    zeroRawPIIVerified: bool
    validationDetails: List[str]

class SanitizedContextPayload(BaseModel):
    taskId: str
    timestamp: int
    originDomain: str
    viewport: Dict[str, int]
    sanitizedDomNodes: List[DOMNodeDescriptor]
    maskedScreenshotBase64: Optional[str] = None
    boundaryReport: PrivacyBoundaryReport

class ActionTarget(BaseModel):
    nodeId: Optional[str] = None
    selector: Optional[str] = None
    xpath: Optional[str] = None

class StructuredAction(BaseModel):
    actionId: str
    taskId: str
    action: str  # CLICK, TYPE, SELECT, SCROLL, NAVIGATE, HOVER, WAIT
    target: ActionTarget
    value: Optional[str] = None
    confidence: float
    reasoning: str
