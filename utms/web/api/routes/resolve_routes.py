from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body, Request
from fastapi.responses import HTMLResponse
from utms.web.api.models import config
from utms.web.api import templates
from utms import AI
from utms.utils import ansi_to_html

router = APIRouter()

@router.get("/resolve", response_class=HTMLResponse)
async def resolve_page(request: Request):
    # Get all available anchors for selection
    anchors_data = {}
    for anchor in config.anchors._anchors.values():
        anchors_data[anchor.label] = {
            "name": anchor.name,
            "formats": [format_spec.__dict__ for format_spec in anchor.formats],
        }
    
    return templates.TemplateResponse(
        "resolve.html",
        {
            "request": request,
            "active_page": "resolve",
            "anchors": anchors_data
        }
    )

@router.get("/")
async def get_resolve_info():
    # Basic endpoint for initial data if needed
    return {"status": "active"}

@router.post("/resolve")
async def resolve_time(data: dict):
    try:
        input_string = data.get("input")
        selected_anchors = data.get("anchors", [])
        
        if not input_string:
            raise HTTPException(status_code=400, detail="No input string provided")

        # Use AI to resolve the date
        ai = AI(config)
        parsed_timestamp = ai.resolve_date(input_string)

        if not parsed_timestamp:
            raise HTTPException(status_code=400, detail="Could not resolve the time expression")

        # Convert to total seconds if it's a datetime
        total_seconds = (
            Decimal(parsed_timestamp.timestamp()) 
            if isinstance(parsed_timestamp, datetime) 
            else parsed_timestamp
        )

        # Get the resolved datetime for display
        resolved_date = (
            parsed_timestamp 
            if isinstance(parsed_timestamp, datetime)
            else datetime.fromtimestamp(float(total_seconds))
        )

        # Get results for each selected anchor
        results = {}
        for anchor_label in selected_anchors:
            anchor = config.anchors.get(anchor_label)
            if not anchor:
                continue

            # Calculate the difference and format it
            diff_seconds = total_seconds - anchor.value
            formatted_results = anchor.format(diff_seconds, config.units)

            results[anchor_label] = {
                "name": anchor.name,
                "formats": [ansi_to_html(line) for line in formatted_results.split('\n')] if formatted_results else []
            }

        return {
            "status": "success",
            "resolved_date": resolved_date.isoformat(),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
