from venv import logger

from mcstatus import BedrockServer, JavaServer
from mcstatus.motd import Motd
from mcstatus.status_response import BedrockStatusResponse, JavaStatusResponse


async def get_server_stats(host: str, server_type: str):
    """
    Retrieves the status of a Minecraft server (either Java or Bedrock).

    Args:
        host (str): The hostname or IP address of the server to query.
        server_type (str): The type of the server, either 'java' or 'bedrock'.

    Returns:
        dict: A dictionary containing the server's status or an error message.
    """
    response: JavaStatusResponse | BedrockStatusResponse | None = None
    try:
        if server_type == "JAVA":
            response = await _handle_java_stats(host)
        elif server_type == "BEDROCK":
            response = await _handle_bedrock_stats(host)
        else:
            logger.error(f"Unsupported server type: {server_type}; host: {host}")
            raise ValueError("Unsupported server type")

        return format_response(response)
    except Exception:
        return None


async def _handle_java_stats(host: str) -> JavaStatusResponse:
    """
    Pings a Java Minecraft server and returns its status.

    Args:
        host (str): The hostname or IP address of the Java server to query.

    Returns:
        JavaStatusResponse: The status of the Java Minecraft server.

    Raises:
        ValueError: If the connection to the Java server fails.
    """
    try:
        server = await JavaServer.async_lookup(host)
        return await server.async_status()
    except Exception as e:
        raise ValueError(f"Failed to connect to Java server at {host}: {e}") from e


async def _handle_bedrock_stats(host: str) -> BedrockStatusResponse:
    """
    Pings a Bedrock Minecraft server and returns its status.

    Args:
        host (str): The hostname or IP address of the Bedrock server to query.

    Returns:
        BedrockStatusResponse: The status of the Bedrock Minecraft server.

    Raises:
        ValueError: If the connection to the Bedrock server fails.
    """
    try:
        server = BedrockServer.lookup(host)
        return await server.async_status()
    except Exception as e:
        raise ValueError(f"Failed to connect to Bedrock server at {host}: {e}") from e


def format_response(response: JavaStatusResponse | BedrockStatusResponse) -> dict:
    """
    Formats the server status response into a dictionary with the required structure.

    Args:
        response (JavaStatusResponse | BedrockStatusResponse): The server status response.

    Returns:
        dict: A dictionary containing the formatted server status information.
    """
    if isinstance(response, JavaStatusResponse):
        return {
            "online": True,
            "players": {
                "online": response.players.online,
                "max": response.players.max,
            },
            "delay": response.latency,
            "version": response.version.name,
            "motd": format_motd(response.motd),
            "icon": response.icon,
        }
    elif isinstance(response, BedrockStatusResponse):
        return {
            "online": True,
            "players": {
                "online": response.players.online,
                "max": response.players.max,
            },
            "delay": response.latency,
            "version": response.version.name,
            "motd": format_motd(response.motd),
            "icon": None,
        }
    else:
        raise ValueError("Unexpected response type")


def format_motd(motd: Motd) -> dict:
    """
    Helper function to format the Message of the Day (MOTD) into various formats.

    Args:
        motd: The MOTD object that contains the server's message.

    Returns:
        dict: A dictionary with the MOTD in different formats such as plain, HTML, Minecraft, and ANSI.
    """
    return {
        "plain": motd.to_plain(),
        "html": motd.to_html(),
        "minecraft": motd.to_minecraft(),
        "ansi": motd.to_ansi(),
    }
