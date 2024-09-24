import disnake
from disnake.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Показать список серверов и пользователей")
    async def show_servers(self, inter: disnake.ApplicationCommandInteraction):
        guilds_info = ""
        for guild in self.bot.guilds:
            guilds_info += f"Сервер: {guild.name} (ID: {guild.id})\n"
            for member in guild.members:
                guilds_info += f" - {member.name}#{member.discriminator} (ID: {member.id})\n"
        await inter.send(f"Список серверов и пользователей:\n{guilds_info}", ephemeral=True)

def setup(bot):
    bot.add_cog(Admin(bot))
