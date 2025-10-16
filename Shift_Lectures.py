# Import module
try:
    import requests
    from decouple import config
    from datetime import datetime
    from pytz import FixedOffset, UTC
    import os
    import json
    from dateutil import parser
    from dateutil import parser
    from datetime import timedelta
    # from pathlib import Path, resolve
except:
    print("failed to import libraries")

def initializeConfigurations():
    """
    Initialize and return configuration values.
    """
    notionToken = config("NOTION_TOKEN")
    notionDatabaseId = config("NOTION_DATEBASE_LECTURES_ID")
    apiUrl = f"https://api.notion.com/v1/databases/{notionDatabaseId}/query"
    headers = {
        "Authorization": f"Bearer {notionToken}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    return notionDatabaseId, headers, apiUrl

notionDatabaseId, headers, apiUrl = initializeConfigurations()

def fetchItems(pageSize: int = None):
    """
    Fetch a list of items from the Notion database.
    """
    pageSize = 100 if pageSize is None else pageSize
    payload = {"page_size": pageSize}
    response = requests.post(apiUrl, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get('results', [])
    else:
        print(f"Failed to request. Status code: {response.status_code}")
        return []
def shiftDateAWeek(stringDate):
    date = parser.isoparse(stringDate)
    shiftedDate = date + timedelta(weeks=1)
    output = shiftedDate.isoformat()
    return output



def shiftLectures():
    """
    Shift Lectures one week every week.
    """
    lectures = fetchItems()
    count = 0
    for lecture in lectures:
        startDateStr = lecture['properties']['Date']['date']['start']
        endDateStr = lecture['properties']['Date']['date']["end"]
        shiftedStartDate = shiftDateAWeek(startDateStr)
        shiftedEndDate = shiftDateAWeek(endDateStr)
        data = {'properties': {"Date" : {"date": {"start": f"{shiftedStartDate}","end": f"{shiftedEndDate}",}}}}
        itemUrl = f'https://api.notion.com/v1/pages/{lecture["id"]}'
        response = requests.patch(itemUrl, headers=headers, json=data)
        # Check the response
        if response.status_code == 200:
            print(f"Item N.{count + 1} updated successfully.")
            count += 1
        else:
            print('Failed to update item:', response.json())
            
    if count == len(lectures):
        print("Successfully updated all items!")
    else:
        print(f"Failed to update {len(lectures) - count} items!")


        
if __name__ == "__main__":
    shiftLectures()