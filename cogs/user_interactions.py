import disnake
from disnake.ext import commands
import config
from typing import Dict, Optional

user_data: Dict[int, Dict[str, Optional[str]]] = {}

class UserInteractions(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        if isinstance(message.channel, disnake.DMChannel) and not message.author.bot:
            guild: Optional[disnake.Guild] = self.bot.get_guild(config.REVIEW_SERVER_ID)
            if not guild:
                await message.author.send("Сервер не знайдено.")
                return

            member: Optional[disnake.Member] = guild.get_member(message.author.id)
            if not member:
                await message.author.send("Ви не є учасником цього сервера.")
                return

            if config.REQUIRED_ROLE_ID not in [role.id for role in member.roles]:
                await message.author.send("У вас немає необхідної ролі.")
                return

            user_data[message.author.id] = {
                "text": message.content,
                "attachment": message.attachments[0].url if message.attachments else None,
                "author": str(message.author)
            }

            buttons = [
                disnake.ui.Button(label="Оголошення", custom_id="bonfire:channels/announcement", emoji="📣"),
                disnake.ui.Button(label="Торгівля", custom_id="bonfire:channels/trade", emoji="💸"),
            ]
            if message.attachments:
                buttons.append(disnake.ui.Button(label="Скріншоти", custom_id="bonfire:channels/screenshot", emoji="📸"))

            try:
                response: disnake.Message = await message.author.send(
                    "В який канал хочете опубліковати?", 
                    components=[
                        disnake.ui.ActionRow(*buttons)
                    ]
                )
                user_data[message.author.id]["message_id"] = str(response.id)
            except disnake.Forbidden:
                await message.author.send("Не можу відправити повідомлення. Упевніться, що у мене є необхідні дозволи.")

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction) -> None:
        custom_id: str = inter.component.custom_id
        user_id: int = inter.author.id
        guild: Optional[disnake.Guild] = self.bot.get_guild(config.REVIEW_SERVER_ID)
        if not guild:
            await inter.response.send_message("Гільдія не знайдена.", ephemeral=True)
            return

        member: Optional[disnake.Member] = guild.get_member(user_id)
        if not member:
            await inter.response.send_message("Ви не є учасником цього сервера.", ephemeral=True)
            return

        if custom_id in config.CHANNELS:
            if config.REQUIRED_ROLE_ID not in [role.id for role in member.roles]:
                await inter.response.send_message("У вас немає прав на використання цієї кнопки.", ephemeral=True)
                return

            section_name: str = {
                "bonfire:channels/announcement": "Оголошення",
                "bonfire:channels/trade": "Торгівля",
                "bonfire:channels/screenshot": "Скріншоти"
            }.get(custom_id, "Невідомий розділ")

            buttons = [
                disnake.ui.Button(label="Оголошення", custom_id="bonfire:channels/announcement", emoji="📣", disabled=True),
                disnake.ui.Button(label="Торгівля", custom_id="bonfire:channels/trade", emoji="💸", disabled=True),
            ]
            if user_data[user_id]["attachment"]:
                buttons.append(disnake.ui.Button(label="Скріншоти", custom_id="bonfire:channels/screenshot", emoji="📸", disabled=True))

            ad_text: str = user_data[user_id].get("text", "Текст оголошення не знайдено.")
            attachment: Optional[str] = user_data[user_id].get("attachment", None)

            embed: disnake.Embed = disnake.Embed(description=f"{config.RULES[custom_id]}\n\nНазва розділу: {section_name}\n\nТекст оголошення:\n{ad_text}")
            if attachment:
                embed.set_image(url=attachment)

            try:
                original_message: disnake.Message = await inter.author.fetch_message(int(user_data[user_id]["message_id"]))
                await original_message.edit(
                    components=[
                        disnake.ui.ActionRow(*buttons)
                    ]
                )

                confirm_button_disabled: bool = config.REQUIRED_ROLE_ID not in [role.id for role in member.roles]
                response: disnake.Message = await inter.author.send(
                    embed=embed,
                    components=[
                        disnake.ui.ActionRow(
                            disnake.ui.Button(label="Підтвердити", custom_id=f"confirm_{custom_id}", disabled=confirm_button_disabled)
                        )
                    ]
                )
                user_data[user_id]["confirm_message_id"] = str(response.id)
                await inter.response.defer()  # Defers the interaction response
            except disnake.Forbidden:
                await inter.author.send("Не можу відправити повідомлення. Упевніться, що у мене є необхідні дозволи.")

            user_data[user_id]["selected_channel"] = custom_id

        elif custom_id.startswith("confirm_"):
            if user_id not in config.MODERATORS and config.REQUIRED_ROLE_ID not in [role.id for role in member.roles]:
                await inter.response.send_message("У вас немає прав на використання цієї кнопки.", ephemeral=True)
                return

            label: str = custom_id.split("_", 1)[1]
            review_guild: Optional[disnake.Guild] = self.bot.get_guild(config.REVIEW_SERVER_ID)
            review_channel: Optional[disnake.TextChannel] = review_guild.get_channel(config.REVIEW_CHANNEL_ID) if review_guild else None
            if review_channel:
                ad_text: str = user_data.get(user_id, {}).get("text", "Текст оголошення не знайдено.")
                attachment: Optional[str] = user_data.get(user_id, {}).get("attachment", None)
                author: Optional[str] = user_data.get(user_id, {}).get("author")
                section_name: str = {
                    "bonfire:channels/announcement": "Оголошення",
                    "bonfire:channels/trade": "Торгівля",
                    "bonfire:channels/screenshot": "Скріншоти"
                }.get(label, "Невідомий розділ")
                embed: disnake.Embed = disnake.Embed(description=f"Оголошення від {author}:\n{ad_text}\n\nКанал: {section_name}")
                if attachment:
                    embed.set_image(url=attachment)
                try:
                    review_message: disnake.Message = await review_channel.send(embed=embed, components=[
                        disnake.ui.ActionRow(
                            disnake.ui.Button(label="✅ Опубліковать", custom_id=f"approve_{user_id}_{label}"),
                            disnake.ui.Button(label="❌ Повернути", custom_id=f"deny_{user_id}")
                        )
                    ])
                    user_data[user_id]["review_message_id"] = str(review_message.id)
                    await inter.response.send_message("Чекайте, ваш пост в обробці модераторів.", ephemeral=True)
                except disnake.Forbidden:
                    await inter.response.send_message("Не можу відправити повідомлення в канал перевірки. Упевніться, що у мене є необхідні дозволи.", ephemeral=True)

            confirm_message: disnake.Message = await inter.author.fetch_message(int(user_data[user_id]["confirm_message_id"]))
            await confirm_message.edit(
                components=[
                    disnake.ui.ActionRow(
                        disnake.ui.Button(label="Підтвердити", custom_id=f"confirm_{label}", disabled=True)
                    )
                ]
            )

        elif custom_id.startswith("approve_") or custom_id.startswith("deny_"):
            if user_id not in config.MODERATORS:
                await inter.response.send_message("У вас немає прав на використання цієї кнопки.", ephemeral=True)
                return

            parts: list[str] = custom_id.split("_")
            target_user_id: int = int(parts[1])
            label: Optional[str] = parts[2] if custom_id.startswith("approve_") else None
            channel_id: Optional[int] = config.CHANNELS.get(label) if label else None

            review_message: disnake.Message = await inter.channel.fetch_message(int(user_data[target_user_id]["review_message_id"]))
            await review_message.edit(
                components=[
                    disnake.ui.ActionRow(
                        disnake.ui.Button(label="✅ Опубліковать", custom_id=f"approve_{target_user_id}_{label}", disabled=True),
                        disnake.ui.Button(label="❌ Повернути", custom_id=f"deny_{target_user_id}", disabled=True)
                    )
                ]
            )

            if custom_id.startswith("approve_") and channel_id:
                channel: Optional[disnake.TextChannel] = self.bot.get_channel(channel_id)
                if channel:
                    ad_text: str = user_data.get(target_user_id, {}).get("text", "Текст оголошення не знайдено.")
                    attachment: Optional[str] = user_data.get(target_user_id, {}).get("attachment", None)
                    author: Optional[str] = user_data.get(target_user_id, {}).get("author")
                    embed: disnake.Embed = disnake.Embed(description=f"Оголошення від {author}:\n{ad_text}")
                    if attachment:
                        embed.set_image(url=attachment)
                    await channel.send(embed=embed)
                    await inter.response.send_message("Пост опубліковано.")
                    if author:
                        await self.bot.get_user(target_user_id).send("Ваш пост опубліковано!")
                    user_data.pop(target_user_id, None)

            elif custom_id.startswith("deny_"):
                author: Optional[str] = user_data.get(target_user_id, {}).get("author")
                await inter.response.send_message("Пост відхилено.")
                if author:
                    await self.bot.get_user(target_user_id).send("Ваш пост відхилено.")
                    user_data.pop(target_user_id, None)

def setup(bot: commands.Bot) -> None:
    bot.add_cog(UserInteractions(bot))
