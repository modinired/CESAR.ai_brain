"""
Comprehensive Multi-Agent Learning Flow with Prefect
Orchestrates scraping, processing, embedding, and reflection generation
"""

from prefect import flow, task, get_run_logger
import psycopg2
from psycopg2.extras import Json
import os
import requests
from datetime import datetime
from typing import List, Tuple, Dict, Any
import time
from openai import OpenAI

# Environment configuration
DSN = os.environ.get(
    "POSTGRES_DSN",
    "postgresql://mcp_user:change-this-in-production-use-strong-password@postgres:5432/mcp"
)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ============================================================================
# DATABASE UTILITIES
# ============================================================================

def get_db_connection():
    """Get database connection with retry logic"""
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(DSN)
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
            else:
                raise Exception(f"Failed to connect to database after {max_retries} attempts: {e}")

# ============================================================================
# SOURCE FETCHING TASKS
# ============================================================================

@task(retries=2, retry_delay_seconds=5)
def fetch_pending_sources(limit: int = 20) -> List[Tuple[str, str, str]]:
    """Fetch pending learning sources from database"""
    logger = get_run_logger()
    logger.info(f"Fetching up to {limit} pending sources")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, url, source_type
            FROM learning_sources
            WHERE fetch_status = 'pending' AND retry_count < 3
            ORDER BY priority DESC, created_at ASC
            LIMIT %s
        """, (limit,))

        sources = cursor.fetchall()
        logger.info(f"Found {len(sources)} pending sources")
        return sources

    finally:
        cursor.close()
        conn.close()

# ============================================================================
# SCRAPING TASKS
# ============================================================================

@task(retries=3, retry_delay_seconds=10)
def scrape_source(source_id: str, url: str, source_type: str) -> Dict[str, Any]:
    """Scrape content from a single source"""
    logger = get_run_logger()
    logger.info(f"Scraping source: {url}")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Attempt to fetch content
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; MultiAgentLearning/1.0)'
        }

        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()

        content = response.text[:50000]  # Limit content size

        # Basic content extraction based on type
        if source_type in ['article', 'research']:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            text_content = soup.get_text(separator=' ', strip=True)
            title = soup.find('title').get_text() if soup.find('title') else url.split('/')[-1]

        else:
            text_content = content
            title = url.split('/')[-1]

        # Insert material into database
        cursor.execute("""
            INSERT INTO learning_materials (
                source_id, title, description, content,
                word_count, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            source_id,
            title[:500],
            f"Auto-scraped from {source_type}",
            text_content,
            len(text_content.split()),
            Json({"scraped_at": datetime.now().isoformat(), "status_code": response.status_code})
        ))

        material_id = cursor.fetchone()[0]

        # Update source status
        cursor.execute("""
            UPDATE learning_sources
            SET fetch_status = 'fetched',
                last_fetched = NOW(),
                retry_count = 0
            WHERE id = %s
        """, (source_id,))

        conn.commit()

        logger.info(f"Successfully scraped and stored material {material_id}")

        return {
            "success": True,
            "material_id": str(material_id),
            "source_id": str(source_id),
            "word_count": len(text_content.split())
        }

    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")

        # Update source with error
        cursor.execute("""
            UPDATE learning_sources
            SET fetch_status = 'failed',
                fetch_error = %s,
                retry_count = retry_count + 1
            WHERE id = %s
        """, (str(e)[:500], source_id))

        conn.commit()

        return {
            "success": False,
            "source_id": str(source_id),
            "error": str(e)
        }

    finally:
        cursor.close()
        conn.close()

@task
def scrape_all_sources(sources: List[Tuple[str, str, str]]) -> List[Dict[str, Any]]:
    """Scrape all provided sources"""
    logger = get_run_logger()
    logger.info(f"Scraping {len(sources)} sources")

    results = []
    for source_id, url, source_type in sources:
        result = scrape_source(source_id, url, source_type)
        results.append(result)

    successful = sum(1 for r in results if r.get("success"))
    logger.info(f"Scraping complete: {successful}/{len(sources)} successful")

    return results

# ============================================================================
# EMBEDDING GENERATION TASKS
# ============================================================================

@task(retries=2, retry_delay_seconds=5)
def generate_embedding(material_id: str, content: str) -> Dict[str, Any]:
    """Generate embedding for a single material"""
    logger = get_run_logger()
    logger.info(f"Generating embedding for material {material_id}")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Truncate content if too long (OpenAI limit)
        max_tokens = 8000
        truncated_content = content[:max_tokens * 4]  # Rough character estimate

        # Generate embedding
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=truncated_content
        )

        vector = response.data[0].embedding

        # Update material with embedding
        cursor.execute("""
            UPDATE learning_materials
            SET vector = %s, processed = TRUE
            WHERE id = %s
        """, (vector, material_id))

        conn.commit()

        logger.info(f"Successfully generated embedding for material {material_id}")

        return {
            "success": True,
            "material_id": str(material_id),
            "embedding_dimension": len(vector)
        }

    except Exception as e:
        logger.error(f"Error generating embedding for {material_id}: {str(e)}")
        return {
            "success": False,
            "material_id": str(material_id),
            "error": str(e)
        }

    finally:
        cursor.close()
        conn.close()

@task
def generate_embeddings_for_materials(scrape_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate embeddings for all successfully scraped materials"""
    logger = get_run_logger()

    # Filter successful scrapes
    successful_materials = [r for r in scrape_results if r.get("success")]

    if not successful_materials:
        logger.info("No materials to generate embeddings for")
        return []

    logger.info(f"Generating embeddings for {len(successful_materials)} materials")

    conn = get_db_connection()
    cursor = conn.cursor()

    results = []

    for result in successful_materials:
        material_id = result["material_id"]

        # Fetch content
        cursor.execute(
            "SELECT content FROM learning_materials WHERE id = %s",
            (material_id,)
        )
        row = cursor.fetchone()

        if row:
            content = row[0]
            embedding_result = generate_embedding(material_id, content)
            results.append(embedding_result)

    cursor.close()
    conn.close()

    successful = sum(1 for r in results if r.get("success"))
    logger.info(f"Embedding generation complete: {successful}/{len(results)} successful")

    return results

# ============================================================================
# REFLECTION GENERATION TASKS
# ============================================================================

@task(retries=2, retry_delay_seconds=5)
def generate_reflection(material_id: str, content: str, agent_id: str = "agent_reflector") -> Dict[str, Any]:
    """Generate AI reflection on learning material"""
    logger = get_run_logger()
    logger.info(f"Generating reflection for material {material_id}")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Truncate content for prompt
        max_content_length = 8000
        truncated_content = content[:max_content_length]

        # Generate reflection using GPT-4
        prompt = f"""You are an expert learning curator and critical thinker.
Analyze the following learning material and provide:
1. A concise summary (2-3 sentences)
2. 3-5 key insights or takeaways
3. 2-3 critical questions this material raises
4. Suggested applications or next steps

Material:
{truncated_content}

Provide your response in a structured format."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )

        reflection_text = response.choices[0].message.content

        # Extract key insights (simplified - could use more sophisticated parsing)
        key_insights = []
        if "key insights" in reflection_text.lower():
            # Basic extraction logic
            lines = reflection_text.split('\n')
            for i, line in enumerate(lines):
                if 'key insight' in line.lower() or 'takeaway' in line.lower():
                    # Get next few lines
                    key_insights = [l.strip('- ').strip() for l in lines[i+1:i+6] if l.strip()]
                    break

        # Insert reflection
        cursor.execute("""
            INSERT INTO learning_reflections (
                material_id, agent_id, reflection_text,
                reflection_type, reflection_score, key_insights
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            material_id,
            agent_id,
            reflection_text,
            'critical',
            0.85,  # Default quality score
            key_insights[:5] if key_insights else []
        ))

        reflection_id = cursor.fetchone()[0]
        conn.commit()

        logger.info(f"Successfully generated reflection {reflection_id} for material {material_id}")

        return {
            "success": True,
            "material_id": str(material_id),
            "reflection_id": str(reflection_id),
            "key_insights_count": len(key_insights)
        }

    except Exception as e:
        logger.error(f"Error generating reflection for {material_id}: {str(e)}")
        return {
            "success": False,
            "material_id": str(material_id),
            "error": str(e)
        }

    finally:
        cursor.close()
        conn.close()

@task
def generate_reflections_for_materials(embedding_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate reflections for all successfully embedded materials"""
    logger = get_run_logger()

    # Filter successful embeddings
    successful_materials = [r for r in embedding_results if r.get("success")]

    if not successful_materials:
        logger.info("No materials to generate reflections for")
        return []

    logger.info(f"Generating reflections for {len(successful_materials)} materials")

    conn = get_db_connection()
    cursor = conn.cursor()

    results = []

    for result in successful_materials:
        material_id = result["material_id"]

        # Fetch content
        cursor.execute(
            "SELECT content FROM learning_materials WHERE id = %s",
            (material_id,)
        )
        row = cursor.fetchone()

        if row:
            content = row[0]
            reflection_result = generate_reflection(material_id, content)
            results.append(reflection_result)

    cursor.close()
    conn.close()

    successful = sum(1 for r in results if r.get("success"))
    logger.info(f"Reflection generation complete: {successful}/{len(results)} successful")

    return results

# ============================================================================
# LOGGING TASKS
# ============================================================================

@task
def log_workflow_execution(
    workflow_name: str,
    status: str,
    start_time: datetime,
    tasks_total: int,
    tasks_completed: int,
    tasks_failed: int
):
    """Log workflow execution metrics"""
    logger = get_run_logger()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        end_time = datetime.now()
        duration_seconds = int((end_time - start_time).total_seconds())

        cursor.execute("""
            INSERT INTO workflow_metrics (
                workflow_name, status, start_time, end_time,
                duration_seconds, tasks_total, tasks_completed, tasks_failed,
                agent_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            workflow_name, status, start_time, end_time,
            duration_seconds, tasks_total, tasks_completed, tasks_failed,
            "agent_main"
        ))

        conn.commit()

        logger.info(f"Workflow execution logged: {status}, duration: {duration_seconds}s")

    finally:
        cursor.close()
        conn.close()

@task
def update_agent_metrics(agent_id: str, tasks_completed: int, tasks_failed: int):
    """Update agent performance metrics"""
    logger = get_run_logger()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE agent_profile
            SET
                total_tasks_completed = total_tasks_completed + %s,
                success_rate = CASE
                    WHEN total_tasks_completed + %s + %s > 0
                    THEN (total_tasks_completed * success_rate + %s) / (total_tasks_completed + %s + %s)
                    ELSE 0
                END,
                updated_at = NOW()
            WHERE agent_id = %s
        """, (
            tasks_completed,
            tasks_completed, tasks_failed,
            tasks_completed,
            tasks_completed, tasks_failed,
            agent_id
        ))

        conn.commit()

        logger.info(f"Updated metrics for agent {agent_id}")

    finally:
        cursor.close()
        conn.close()

# ============================================================================
# MAIN FLOW
# ============================================================================

@flow(name="daily_recursive_learning_full", log_prints=True)
def daily_recursive_learning_full(source_limit: int = 20):
    """
    Main orchestration flow for recursive learning system
    """
    logger = get_run_logger()
    start_time = datetime.now()

    logger.info("=" * 80)
    logger.info("Starting Daily Recursive Learning Flow")
    logger.info("=" * 80)

    try:
        # Step 1: Fetch pending sources
        logger.info("\n[STEP 1] Fetching pending sources...")
        sources = fetch_pending_sources(limit=source_limit)

        if not sources:
            logger.info("No pending sources found. Workflow complete.")
            log_workflow_execution(
                "daily_recursive_learning_full", "completed", start_time, 0, 0, 0
            )
            return {"status": "completed", "message": "No sources to process"}

        # Step 2: Scrape sources
        logger.info(f"\n[STEP 2] Scraping {len(sources)} sources...")
        scrape_results = scrape_all_sources(sources)
        successful_scrapes = sum(1 for r in scrape_results if r.get("success"))

        # Step 3: Generate embeddings
        logger.info(f"\n[STEP 3] Generating embeddings for {successful_scrapes} materials...")
        embedding_results = generate_embeddings_for_materials(scrape_results)
        successful_embeddings = sum(1 for r in embedding_results if r.get("success"))

        # Step 4: Generate reflections
        logger.info(f"\n[STEP 4] Generating reflections for {successful_embeddings} materials...")
        reflection_results = generate_reflections_for_materials(embedding_results)
        successful_reflections = sum(1 for r in reflection_results if r.get("success"))

        # Step 5: Update metrics
        logger.info("\n[STEP 5] Updating agent and workflow metrics...")
        total_tasks = len(sources)
        completed_tasks = successful_reflections
        failed_tasks = total_tasks - completed_tasks

        update_agent_metrics("agent_main", completed_tasks, failed_tasks)

        log_workflow_execution(
            "daily_recursive_learning_full",
            "completed",
            start_time,
            total_tasks,
            completed_tasks,
            failed_tasks
        )

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("WORKFLOW SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Sources processed: {len(sources)}")
        logger.info(f"Successful scrapes: {successful_scrapes}")
        logger.info(f"Successful embeddings: {successful_embeddings}")
        logger.info(f"Successful reflections: {successful_reflections}")
        logger.info(f"Duration: {int((datetime.now() - start_time).total_seconds())}s")
        logger.info("=" * 80)

        return {
            "status": "completed",
            "total_sources": len(sources),
            "successful_scrapes": successful_scrapes,
            "successful_embeddings": successful_embeddings,
            "successful_reflections": successful_reflections,
            "duration_seconds": int((datetime.now() - start_time).total_seconds())
        }

    except Exception as e:
        logger.error(f"Workflow failed: {str(e)}")

        log_workflow_execution(
            "daily_recursive_learning_full",
            "failed",
            start_time,
            0, 0, 1
        )

        raise


if __name__ == "__main__":
    # For local testing
    daily_recursive_learning_full(source_limit=5)
