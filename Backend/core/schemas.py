from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

# --- Shared Models ---

class KPI(BaseModel):
    id: str
    label: str
    value: float
    sql: Optional[str] = None

# --- Analytics Agent Models ---

class AnalyticsInput(BaseModel):
    dataset_id: str
    column_profiles: Union[Dict[str, Any], List[Dict[str, Any]]]
    file_path: str
    business_context: Optional[str] = None

class AggregateItem(BaseModel):
    table_ref: str
    description: Optional[str] = None
    recommended_chart: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None # Actual data rows

class ForecastItem(BaseModel):
    series: str
    forecast_values: List[float]
    period: str  # e.g., "Next 3 Months"

class AnomalyItem(BaseModel):
    row_index: int
    column: str
    value: float
    z_score: float

class RiskAnalysis(BaseModel):
    risk_score: float  # 0-100
    risk_level: str    # "Low", "Medium", "High"
    reason: str

class RFMSegment(BaseModel):
    segment_name: str
    count: int
    avg_monetary: float
    description: str

class BasketRule(BaseModel):
    antecedents: List[str]
    consequents: List[str]
    confidence: float
    lift: float

class AnalyticsOutput(BaseModel):
    model_config = ConfigDict(extra='ignore')
    dataset_id: str
    kpis: List[KPI]
    aggregates: Dict[str, AggregateItem]
    forecasts: Optional[List[ForecastItem]] = None
    anomalies: Optional[List[AnomalyItem]] = None
    risk_analysis: Optional[RiskAnalysis] = None
    rfm_analysis: Optional[List[RFMSegment]] = None
    basket_analysis: Optional[List[BasketRule]] = None
    recommendations: Optional[List[str]] = None


# --- UI Controller Agent Models ---

class UIComponent(BaseModel):
    id: str
    type: str  # e.g., "kpi", "bar_chart", "line_chart", "table", "decision_list"
    title: str
    visible: bool = True
    col_span: Optional[int] = None  # 1 to 4 (Full Width)
    description: Optional[str] = None
    subtitle: Optional[str] = None
    width: Optional[str] = None # 'full', 'half'
    
    # Specific fields for charts (optional as not all components need them)
    value_ref: Optional[str] = None  # For KPIs
    data_ref: Optional[str] = None   # For Charts/Tables/Decisions
    x: Optional[str] = None          # For Charts
    y: Optional[str] = None          # For Charts
    drillable: Optional[bool] = False # For Charts
    data: Optional[Any] = None # The actual data payload to be rendered

class SessionContext(BaseModel):
    kpi_list: List[str]
    filters: Dict[str, Any] = Field(default_factory=dict)

class UIControllerInput(BaseModel):
    dataset_id: str
    kpis: List[KPI]
    aggregates: Dict[str, Any]
    forecasts: Optional[List[ForecastItem]] = None
    anomalies: Optional[List[AnomalyItem]] = None
    risk_analysis: Optional[RiskAnalysis] = None
    rfm_analysis: Optional[List[RFMSegment]] = None
    basket_analysis: Optional[List[BasketRule]] = None
    recommendations: Optional[List[str]] = None

    available_components: List[str]
    screen_space: str

class UIControllerOutput(BaseModel):
    model_config = ConfigDict(extra='ignore')
    dashboard_id: str
    components: List[UIComponent]
    session_context: SessionContext
    recommendations: Optional[List[str]] = None
