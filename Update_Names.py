# Import necessary modules
try:
    import requests
    from decouple import config
    from datetime import datetime
    from pytz import FixedOffset, UTC
    import os
    import json
except ImportError:
    print("Failed to import required libraries.")

def initializeConfigurations():
    """
    Initialize and return configuration values.
        * The token.
        * The database ID.
        * The URL.
        * The timezone offset.
        * The headers for the request.
        * The JSON file path.
    """
    tzOffset = FixedOffset(180)
    jsonPath = os.path.abspath(__file__).replace("Update_Names.py", "json/file.json")

    notionToken = config("NOTION_TOKEN")
    notionDatabaseId = config("NOTION_DATEBASE_LECTURES_ID")
    apiUrl = f"https://api.notion.com/v1/databases/{notionDatabaseId}/query"
    headers = {
        "Authorization": f"Bearer {notionToken}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    return notionDatabaseId, headers, apiUrl, tzOffset, jsonPath

notionDatabaseId, headers, apiUrl, tzOffset, jsonPath = initializeConfigurations()

def fetchItems(pageSize: int = None):
    """
    Fetch a list of all items in the Notion database.
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

def safe_get(d, path, default=""):
    """
    Safely get nested values from a dictionary.
    `path` is a list of keys/indexes to traverse.
    """
    for key in path:
        try:
            d = d[key]
        except (KeyError, IndexError, TypeError):
            return default
    return d

def getLecturesNewName():
    """
    Returns a list of lecture IDs with their new names.
    """
    lectures = fetchItems()
    renamedLectures = []
    for lecture in lectures:
        lectureId = safe_get(lecture, ["id"])
        code = safe_get(lecture, ["properties", "Code", "rollup", "array", 0, "rich_text", 0, "text", "content"])
        number = safe_get(lecture, ["properties", "N.", "number"])
        day = safe_get(lecture, ["properties", "Day", "formula", "string"])
        startDateStr = safe_get(lecture, ["properties", "Date", "date", "start"])
        endDateStr = safe_get(lecture, ["properties", "Date", "date", "end"])
        building = safe_get(lecture, ["properties", "Building", "rollup", "array", 0, "rich_text", 0, "text", "content"])
        room = safe_get(lecture, ["properties", "Room", "rollup", "array", 0, "rich_text", 0, "text", "content"])
        division = safe_get(lecture, ["properties", "Division", "rollup", "array", 0, "rich_text", 0, "text", "content"])
        startDateUtc = datetime.fromisoformat(startDateStr).astimezone(UTC)
        endDateUtc = datetime.fromisoformat(endDateStr).astimezone(UTC)
        startDateLocal = startDateUtc.astimezone(tzOffset)
        endDateLocal = endDateUtc.astimezone(tzOffset)
        startDateFormatted = startDateLocal.strftime("%m/%d %I:%M %p")
        endDateFormatted = endDateLocal.strftime("%I:%M %p")
        newName = (f"Lecture {code} | N.{number} | AT {day} | "
                   f"{startDateFormatted} - {endDateFormatted} | IN B.{building} R.{room} | D.{division}")
        renamedLectures.append({"id": lectureId, "newName": newName})
    return True, renamedLectures

def loadJson(filePath):
    if os.path.exists(filePath):
        with open(filePath, 'r') as file:
            return json.load(file)
    return None

def saveJson(filePath, data):
    with open(filePath, 'w') as file:
        json.dump(data, file, indent=4)

def checkIfThereIsAChange():
    newData = fetchItems()
    # Load the old JSON data
    oldData = loadJson(jsonPath)
    
    # Compare old data with new data
    if oldData == newData:
        return False  # No changes, return False

    # Save the new data since it's different
    saveJson(jsonPath, newData)
    return True  # Data is different, return True

def updateLectures():
    """
    Updates the names of the lectures in the database.
    """
    if checkIfThereIsAChange():  # Check if there are changes in the data
        print("Changes detected. Updating lectures...")
        isJobComplete, renamedLectures = getLecturesNewName()
        if isJobComplete:
            count = 0
            for lecture in renamedLectures:
                itemUrl = f'https://api.notion.com/v1/pages/{lecture["id"]}'
                data = {'properties': {'Name': {'title': [{'text': {'content': lecture["newName"]}}]}}}
                response = requests.patch(itemUrl, headers=headers, json=data)
                # Check the response
                if response.status_code == 200:
                    print(f"Item N.{count + 1} updated successfully.")
                    count += 1
                else:
                    print('Failed to update item:', response.json())

            if count == len(renamedLectures):
                print("Successfully updated all items!")
            else:
                print(f"Failed to update {len(renamedLectures) - count} items!")
        else:
            print("Failed to fetch lectures.")

if __name__ == "__main__":
    updateLectures()
