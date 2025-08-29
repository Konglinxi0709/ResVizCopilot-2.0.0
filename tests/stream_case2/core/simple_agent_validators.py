"""
SimpleAgent的验证器模型
定义不同提示词类型对应的验证器
"""
from typing import Optional
from pydantic import BaseModel, Field, validator


class CreateResearchProblemOutput(BaseModel):
    """创建研究问题的输出验证器"""
    title: str = Field(..., description="行动标题，固定为create_research_problem")
    params: "CreateResearchProblemParams" = Field(..., description="参数对象")
    
    @validator('title')
    def validate_title(cls, v):
        if v != "create_research_problem":
            raise ValueError('行动标题必须是create_research_problem')
        return v


class CreateResearchProblemParams(BaseModel):
    """创建研究问题的参数验证器"""
    title: str = Field(..., description="研究问题标题")
    significance: str = Field(..., description="研究意义")
    criteria: str = Field(..., description="研究标准")
    
    @validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError('标题长度不能少于5个字符')
        return v.strip()
    
    @validator('significance')
    def validate_significance(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('研究意义描述不能少于10个字符')
        return v.strip()
    
    @validator('criteria')
    def validate_criteria(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError('研究标准不能少于5个字符')
        return v.strip()


class QueryProblemsOutput(BaseModel):
    """查询问题的输出验证器"""
    title: str = Field(..., description="行动标题，固定为query_problems")
    params: "QueryProblemsParams" = Field(..., description="参数对象")
    
    @validator('title')
    def validate_title(cls, v):
        if v != "query_problems":
            raise ValueError('行动标题必须是query_problems')
        return v


class QueryProblemsParams(BaseModel):
    """查询问题的参数验证器"""
    keyword: Optional[str] = Field(None, description="搜索关键词")
    limit: Optional[int] = Field(10, description="结果限制数量")
    
    @validator('limit')
    def validate_limit(cls, v):
        if v is not None and (v < 1 or v > 100):
            raise ValueError('结果限制数量必须在1-100之间')
        return v


class UpdateProblemOutput(BaseModel):
    """更新问题的输出验证器"""
    title: str = Field(..., description="行动标题，固定为update_problem")
    params: "UpdateProblemParams" = Field(..., description="参数对象")
    
    @validator('title')
    def validate_title(cls, v):
        if v != "update_problem":
            raise ValueError('行动标题必须是update_problem')
        return v


class UpdateProblemParams(BaseModel):
    """更新问题的参数验证器"""
    id: str = Field(..., description="问题ID")
    title: Optional[str] = Field(None, description="新标题")
    significance: Optional[str] = Field(None, description="新研究意义")
    criteria: Optional[str] = Field(None, description="新研究标准")
    
    @validator('id')
    def validate_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('问题ID不能为空')
        return v.strip()


# 更新前向引用
CreateResearchProblemOutput.model_rebuild()
QueryProblemsOutput.model_rebuild()
UpdateProblemOutput.model_rebuild()
