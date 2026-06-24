import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import httpx


mcp = FastMCP(
    "University MCP"
)
load_dotenv()

BASE_URL = "http://127.0.0.1:8000"

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

async def get_token():

    async with httpx.AsyncClient() as client:

        request_body = {
            "username": USERNAME,
            "password": PASSWORD
        }

        response = await client.post(
            f"{BASE_URL}/user/api/v1/login",
            json=request_body
        )

        response.raise_for_status()
        result =  response.json()
        print(result)
        return result.get("access_token")


@mcp.tool(description="Use this tool to get the list of departments")
async def get_departments():
    token = await get_token()
    print(token)
    header = {
        "Authorization": f"Bearer {token}"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/department/api/v1",
            headers=header
        )

        return response.json()


@mcp.tool(description="Use this tool to create a new departments")
async def create_departments(department_name : str):
    request_body = {"name":department_name}
    token = await get_token()
    header = {
        "Authorization": f"Bearer {token}"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/department/api/v1/create",
            headers=header,
            json=request_body
        )

        return response.json()

if __name__ == "__main__":
    mcp.run()
