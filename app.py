"""亿日供方开发管理平台"""
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_db() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="数据库未配置")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="亿日供方开发管理平台")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class SupplierCreate(BaseModel):
    supplier_code: str
    supplier_name: str
    supplier_type: str = "raw_material"
    short_name: Optional[str] = None
    category_id: Optional[int] = None
    unified_credit_code: Optional[str] = None
    registered_capital: Optional[str] = None
    legal_representative: Optional[str] = None
    registered_address: Optional[str] = None
    business_scope: Optional[str] = None
    main_products: Optional[str] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[str] = None
    website: Optional[str] = None
    certification: Optional[str] = None
    remarks: Optional[str] = None

class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = None
    short_name: Optional[str] = None
    supplier_type: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[str] = None
    unified_credit_code: Optional[str] = None
    registered_capital: Optional[str] = None
    legal_representative: Optional[str] = None
    registered_address: Optional[str] = None
    business_scope: Optional[str] = None
    main_products: Optional[str] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[str] = None
    website: Optional[str] = None
    certification: Optional[str] = None
    remarks: Optional[str] = None

class StatusUpdate(BaseModel):
    status: str

class EvaluationCreate(BaseModel):
    evaluator: str
    evaluation_type: str = "periodic"
    quality_score: Optional[float] = None
    delivery_score: Optional[float] = None
    service_score: Optional[float] = None
    price_score: Optional[float] = None
    technology_score: Optional[float] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    remarks: Optional[str] = None

class CategoryCreate(BaseModel):
    category_name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class DevelopmentCreate(BaseModel):
    project_name: str
    target_product: Optional[str] = None
    description: Optional[str] = None
    responsible_person: Optional[str] = None
    start_date: Optional[str] = None
    target_end_date: Optional[str] = None
    risks: Optional[str] = None
    milestones: Optional[str] = None

class ContactCreate(BaseModel):
    contact_name: str
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_primary: bool = False
    remarks: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(html_path)

@app.get("/api/suppliers")
async def list_suppliers(status: Optional[str] = None, supplier_type: Optional[str] = None, keyword: Optional[str] = None, page: int = 1, page_size: int = 50):
    db = get_db()
    try:
        query = db.table("suppliers").select("id, supplier_code, supplier_name, short_name, supplier_type, status, main_products, registered_capital, certification, created_at", count="exact")
        if status: query = query.eq("status", status)
        if supplier_type: query = query.eq("supplier_type", supplier_type)
        if keyword: query = query.or_(f"supplier_name.ilike.%{keyword}%,supplier_code.ilike.%{keyword}%")
        offset = (page - 1) * page_size
        response = query.order("created_at", desc=True).range(offset, offset + page_size - 1).execute()
        return {"success": True, "total": response.count, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/suppliers/{supplier_id}")
async def get_supplier(supplier_id: int):
    db = get_db()
    try:
        response = db.table("suppliers").select("*").eq("id", supplier_id).maybe_single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="供应商不存在")
        return {"success": True, "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/suppliers")
async def create_supplier(supplier: SupplierCreate):
    db = get_db()
    try:
        data = supplier.dict(exclude_none=True)
        response = db.table("suppliers").insert(data).execute()
        return {"success": True, "data": response.data[0]}
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail="供应商编码已存在")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/suppliers/{supplier_id}")
async def update_supplier(supplier_id: int, supplier: SupplierUpdate):
    db = get_db()
    try:
        data = supplier.dict(exclude_none=True)
        if not data:
            raise HTTPException(status_code=400, detail="未提供更新字段")
        response = db.table("suppliers").update(data).eq("id", supplier_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="供应商不存在")
        return {"success": True, "data": response.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/suppliers/{supplier_id}/status")
async def update_supplier_status(supplier_id: int, status_update: StatusUpdate):
    valid_statuses = ["potential", "under_review", "qualified", "disqualified", "blacklisted"]
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态，可选值：{valid_statuses}")
    db = get_db()
    try:
        response = db.table("suppliers").update({"status": status_update.status}).eq("id", supplier_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="供应商不存在")
        return {"success": True, "data": response.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: int):
    db = get_db()
    try:
        db.table("supplier_contacts").delete().eq("supplier_id", supplier_id).execute()
        db.table("supplier_evaluations").delete().eq("supplier_id", supplier_id).execute()
        db.table("supplier_developments").delete().eq("supplier_id", supplier_id).execute()
        response = db.table("suppliers").delete().eq("id", supplier_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="供应商不存在")
        return {"success": True, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/suppliers/{supplier_id}/contacts")
async def get_contacts(supplier_id: int):
    db = get_db()
    try:
        response = db.table("supplier_contacts").select("*").eq("supplier_id", supplier_id).order("is_primary", desc=True).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/suppliers/{supplier_id}/contacts")
async def create_contact(supplier_id: int, contact: ContactCreate):
    db = get_db()
    try:
        data = contact.dict(exclude_none=True)
        data["supplier_id"] = supplier_id
        response = db.table("supplier_contacts").insert(data).execute()
        return {"success": True, "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/suppliers/{supplier_id}/evaluations")
async def get_evaluations(supplier_id: int, evaluation_type: Optional[str] = None, limit: int = 20):
    db = get_db()
    try:
        query = db.table("supplier_evaluations").select("*").eq("supplier_id", supplier_id)
        if evaluation_type: query = query.eq("evaluation_type", evaluation_type)
        response = query.order("evaluation_date", desc=True).limit(limit).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/suppliers/{supplier_id}/evaluations")
async def create_evaluation(supplier_id: int, evaluation: EvaluationCreate):
    db = get_db()
    try:
        scores = {"quality": evaluation.quality_score, "delivery": evaluation.delivery_score, "service": evaluation.service_score, "price": evaluation.price_score, "technology": evaluation.technology_score}
        weights = {"quality": 0.30, "delivery": 0.25, "service": 0.15, "price": 0.20, "technology": 0.10}
        total_score = None
        weighted_sum = 0
        weight_total = 0
        for key, weight in weights.items():
            s = scores.get(key)
            if s is not None:
                weighted_sum += s * weight
                weight_total += weight
        if weight_total > 0:
            total_score = round(weighted_sum / weight_total, 2)
        evaluation_result = None
        if total_score is not None:
            if total_score >= 90: evaluation_result = "excellent"
            elif total_score >= 75: evaluation_result = "good"
            elif total_score >= 60: evaluation_result = "average"
            else: evaluation_result = "poor"
        data = evaluation.dict(exclude_none=True)
        data["supplier_id"] = supplier_id
        if total_score is not None: data["total_score"] = total_score
        if evaluation_result is not None: data["evaluation_result"] = evaluation_result
        response = db.table("supplier_evaluations").insert(data).execute()
        return {"success": True, "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/development-projects")
async def list_development_projects(supplier_id: Optional[int] = None, status: Optional[str] = None, stage: Optional[str] = None):
    db = get_db()
    try:
        query = db.table("supplier_developments").select("*")
        if supplier_id is not None: query = query.eq("supplier_id", supplier_id)
        if status: query = query.eq("status", status)
        if stage: query = query.eq("stage", stage)
        response = query.order("created_at", desc=True).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/development-projects")
async def create_development_project(supplier_id: int, project: DevelopmentCreate):
    db = get_db()
    try:
        data = project.dict(exclude_none=True)
        data["supplier_id"] = supplier_id
        response = db.table("supplier_developments").insert(data).execute()
        return {"success": True, "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/development-projects/{project_id}")
async def update_development_project(project_id: int, updates: dict):
    db = get_db()
    try:
        response = db.table("supplier_developments").update(updates).eq("id", project_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="项目不存在")
        return {"success": True, "data": response.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
async def list_categories():
    db = get_db()
    try:
        response = db.table("supplier_categories").select("*").order("category_name").execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/categories")
async def create_category(category: CategoryCreate):
    db = get_db()
    try:
        data = category.dict(exclude_none=True)
        response = db.table("supplier_categories").insert(data).execute()
        return {"success": True, "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics")
async def get_statistics():
    db = get_db()
    try:
        total_resp = db.table("suppliers").select("*", count="exact").execute()
        total_count = total_resp.count or 0
        status_resp = db.table("suppliers").select("status").execute()
        status_counts = {}
        for item in (status_resp.data or []):
            s = item.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1
        type_resp = db.table("suppliers").select("supplier_type").execute()
        type_counts = {}
        for item in (type_resp.data or []):
            t = item.get("supplier_type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        eval_resp = db.table("supplier_evaluations").select("*", count="exact").execute()
        eval_count = eval_resp.count or 0
        dev_resp = db.table("supplier_developments").select("*", count="exact").execute()
        dev_count = dev_resp.count or 0
        return {"success": True, "data": {"total_suppliers": total_count, "by_status": status_counts, "by_type": type_counts, "total_evaluations": eval_count, "total_developments": dev_count}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok", "service": "亿日供方开发管理平台"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
