from initializer.engine.archetype_engine import detect_archetype


# -------------------------------------------------------
# Editorial CMS
# -------------------------------------------------------

def test_detect_editorial_cms_from_cms_prompt():
    result = detect_archetype("Editorial CMS with admin panel and public website")
    assert result["id"] == "editorial-cms"


def test_detect_editorial_cms_from_blog_prompt():
    result = detect_archetype("I want to build a blog with media library and publishing")
    assert result["id"] == "editorial-cms"


def test_detect_editorial_cms_from_content_management():
    result = detect_archetype("content management system for articles and media")
    assert result["id"] == "editorial-cms"


# -------------------------------------------------------
# Marketplace
# -------------------------------------------------------

def test_detect_marketplace_from_marketplace_prompt():
    result = detect_archetype("online marketplace for buying and selling courses")
    assert result["id"] == "marketplace"


def test_detect_marketplace_from_ecommerce_prompt():
    result = detect_archetype("ecommerce store with checkout and cart")
    assert result["id"] == "marketplace"


# -------------------------------------------------------
# SaaS
# -------------------------------------------------------

def test_detect_saas_from_saas_prompt():
    result = detect_archetype("saas application with billing and subscription management")
    assert result["id"] == "saas-app"


def test_detect_saas_from_multitenant_prompt():
    result = detect_archetype("multi-tenant platform with usage tracking and billing")
    assert result["id"] == "saas-app"


# -------------------------------------------------------
# Backoffice
# -------------------------------------------------------

def test_detect_backoffice_from_backoffice_prompt():
    result = detect_archetype("internal backoffice for the operations team to manage orders")
    assert result["id"] == "backoffice"


def test_detect_backoffice_from_operations_prompt():
    result = detect_archetype("operations management tool to generate reports and manage orders")
    assert result["id"] == "backoffice"


def test_detect_backoffice_from_back_office_prompt():
    result = detect_archetype("back office system for internal operations")
    assert result["id"] == "backoffice"


# -------------------------------------------------------
# Client Portal
# -------------------------------------------------------

def test_detect_client_portal_from_portal_prompt():
    result = detect_archetype("client portal where clients can submit requests and track progress")
    assert result["id"] == "client-portal"


def test_detect_client_portal_from_customer_prompt():
    result = detect_archetype("customer portal for request tracking and approvals from internal team")
    assert result["id"] == "client-portal"


# -------------------------------------------------------
# Work Organizer
# -------------------------------------------------------

def test_detect_work_organizer_from_english_prompt():
    result = detect_archetype("work organizer for teams to track tasks and deadlines")
    assert result["id"] == "work-organizer"


def test_detect_work_organizer_from_task_management_prompt():
    result = detect_archetype("task management tool with assignment and sprint tracking")
    assert result["id"] == "work-organizer"


def test_detect_work_organizer_from_portuguese_prompt():
    result = detect_archetype(
        "quero criar algo para empresas organizarem melhor o trabalho delas"
    )
    assert result["id"] == "work-organizer"


def test_detect_work_organizer_from_project_management_prompt():
    result = detect_archetype("project management platform for team workload and deadlines")
    assert result["id"] == "work-organizer"


# -------------------------------------------------------
# Knowledge Base
# -------------------------------------------------------

def test_detect_knowledge_base_from_wiki_prompt():
    result = detect_archetype("internal wiki for team documentation and knowledge sharing")
    assert result["id"] == "knowledge-base"


def test_detect_knowledge_base_from_docs_prompt():
    result = detect_archetype("knowledge base for support articles and FAQ")
    assert result["id"] == "knowledge-base"


# -------------------------------------------------------
# Fallback
# -------------------------------------------------------

def test_detect_generic_fallback():
    result = detect_archetype("I want to build something cool")
    assert result["id"] == "generic-web-app"


def test_detect_generic_for_vague_prompt():
    result = detect_archetype("new application for my company")
    assert result["id"] == "generic-web-app"


# -------------------------------------------------------
# Features and capabilities
# -------------------------------------------------------

def test_backoffice_has_correct_defaults():
    result = detect_archetype("backoffice for operations team")
    assert "authentication" in result["features"]
    assert "roles" in result["features"]
    assert result["capabilities"] == []


def test_client_portal_has_correct_defaults():
    result = detect_archetype("client portal for request tracking")
    assert "authentication" in result["features"]
    assert "roles" in result["features"]
    assert "notifications" in result["features"]


def test_work_organizer_has_correct_defaults():
    result = detect_archetype("work organizer for teams")
    assert "authentication" in result["features"]
    assert "roles" in result["features"]


def test_editorial_cms_has_cms_capability():
    result = detect_archetype("editorial cms with media library")
    assert "cms" in result["capabilities"]
    assert "media-library" in result["features"]