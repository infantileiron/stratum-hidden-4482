from fastapi import HTTPException
from src.constants.enums import ReviewStatus
from src.models.entities import LayerReview
from src.utils import repository as repo
from src.utils.identity import new_id, now
def list_reviews(): return repo.all_rows("reviews")
def create(data,user):
    run=repo.get("runs",data.run_id)
    if run["status"]!="completed":
        if run["status"]=="failed": raise ValueError("运行失败（含复核约束冲突）的结果不能提交复核，请调整约束后新建研究重算")
        raise ValueError("只有已完成的运行可提交复核")
    if run.get("result",{}).get("constraint_conflict"): raise ValueError("存在无法连通孔段的约束冲突结果不能提交复核")
    if any(r["run_id"]==data.run_id and r["status"] in ("pending","approved") for r in repo.all_rows("reviews")): raise HTTPException(409,"该运行已有待审或通过的复核")
    item=LayerReview(new_id("rev"),data.run_id,data.comment,created_at=now())
    return repo.put("reviews",item)
def decide(id,data,user):
    item=repo.get("reviews",id)
    if item["status"]!=ReviewStatus.PENDING.value: raise HTTPException(409,"该复核已处理")
    item.update(status=data.status,comment=data.comment,reviewer=user["email"])
    return repo.put("reviews",item)
