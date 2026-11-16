"""Shapes shared by several routes."""


def avatar_url(discord_id: str, avatar: str | None) -> str | None:
    return f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar}.png" if avatar else None


def user_public(row) -> dict:
    """row needs id (or user_id), discord_id, name, avatar."""
    keys = row.keys()
    return {"id": row["id"] if "id" in keys else row["user_id"], "name": row["name"],
            "avatar_url": avatar_url(row["discord_id"], row["avatar"])}
