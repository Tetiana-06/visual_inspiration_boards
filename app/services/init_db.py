import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, get_engine, get_session_factory
from app.models.user import User
from app.models.board import Board
from app.models.canvas_element import CanvasElement
from app.models.collaborator import BoardCollaborator

logger = logging.getLogger(__name__)


async def init_database():
    """Initializes tables and seeds initial data if database is empty."""
    engine = get_engine()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized.")

    factory = get_session_factory()
    async with factory() as session:
        # Check if users already exist
        users_result = await session.execute(select(User).limit(1))
        if users_result.scalar_one_or_none():
            logger.info("Database already seeded. Skipping initial data population.")
            return

        logger.info("Seeding initial aesthetic demo data (Pinterest Vibe)...")

        # 1. Create Users
        user1 = User(
            email="tetiana.shostak@inspiration.art",
            full_name="Тетяна Шостак",
            avatar_url=None,
        )
        user2 = User(
            email="nataliia.shostak@design.studio",
            full_name="Наталія Шостак",
            avatar_url=None,
        )
        session.add_all([user1, user2])
        await session.flush()

        # 2. Create Board 1: Japandi & Cozy Interior
        board1 = Board(
            title="Wabi-Sabi & Japandi Interior Aesthetics",
            description="Теплі відтінки дерева, льон, кераміка ручної роботи та м'яке розсіяне світло. Дошка натхнення для концепту вітальні.",
            background_color="#F8F4EE",
            grid_type="freeform",
            width=2800,
            height=1800,
            version=1,
            owner_id=user1.id,
        )
        session.add(board1)
        await session.flush()

        # Add collaborator
        collab1 = BoardCollaborator(board_id=board1.id, user_id=user1.id, role="OWNER")
        collab2 = BoardCollaborator(board_id=board1.id, user_id=user2.id, role="EDITOR")
        session.add_all([collab1, collab2])

        # Board 1 Canvas Elements
        el1 = CanvasElement(
            board_id=board1.id,
            element_type="palette",
            x=60,
            y=80,
            width=320,
            height=200,
            z_index=1,
            content={
                "title": "Earth & Sand Harmony",
                "colors": ["#EDE0D4", "#DDB892", "#B08968", "#7F5539", "#463f3a"],
                "tags": ["interior", "neutral", "earth"]
            }
        )
        el2 = CanvasElement(
            board_id=board1.id,
            element_type="image",
            x=410,
            y=60,
            width=360,
            height=440,
            z_index=2,
            content={
                "title": "Japandi Living Room",
                "image_url": "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?w=800&auto=format&fit=crop&q=80",
                "caption": "Мінімалістичний простір, текстури натурального льону",
                "aspect_ratio": "3:4"
            }
        )
        el3 = CanvasElement(
            board_id=board1.id,
            element_type="note",
            x=800,
            y=70,
            width=280,
            height=230,
            z_index=3,
            content={
                "title": "Ідея освітлення",
                "text": "М'яке акцентне світло (2700K) замість яскравої центральної люстри. Паперові абажури у стилі Isamu Noguchi.",
                "color": "#FEF3C7",
                "author": "Тетяна"
            }
        )
        el4 = CanvasElement(
            board_id=board1.id,
            element_type="sticker",
            x=1110,
            y=90,
            width=240,
            height=160,
            z_index=4,
            content={
                "title": "Цитата концепту",
                "text": "✨ Краса у недосконалості та простоті.",
                "color": "#FCE7F3",
                "emoji": "🌿"
            }
        )
        el5 = CanvasElement(
            board_id=board1.id,
            element_type="image",
            x=60,
            y=310,
            width=320,
            height=380,
            z_index=5,
            content={
                "title": "Кераміка ручної роботи",
                "image_url": "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=800&auto=format&fit=crop&q=80",
                "caption": "Матові теракотові та піщані вази",
                "aspect_ratio": "4:5"
            }
        )
        el6 = CanvasElement(
            board_id=board1.id,
            element_type="palette",
            x=800,
            y=330,
            width=320,
            height=200,
            z_index=6,
            content={
                "title": "Sage & Olive Accents",
                "colors": ["#DAD7CD", "#A3B18A", "#588157", "#3A5A40", "#344E41"],
                "tags": ["nature", "accents", "sage"]
            }
        )
        session.add_all([el1, el2, el3, el4, el5, el6])

        # 3. Create Board 2: Autumn Capsule Wardrobe
        board2 = Board(
            title="Autumn Warmth & Editorial Capsule",
            description="Осінні фактури, вовняні пальта, кашемір, вінтажна шкіра та теплі відтінки еспресо й карамелі.",
            background_color="#FBF7F4",
            grid_type="freeform",
            width=2400,
            height=1600,
            version=1,
            owner_id=user2.id,
        )
        session.add(board2)
        await session.flush()

        collab3 = BoardCollaborator(board_id=board2.id, user_id=user2.id, role="OWNER")
        session.add(collab3)

        el7 = CanvasElement(
            board_id=board2.id,
            element_type="image",
            x=80,
            y=70,
            width=340,
            height=430,
            z_index=1,
            content={
                "title": "Wool Coat Silhouette",
                "image_url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&auto=format&fit=crop&q=80",
                "caption": "Вільний крій, колір верблюжої вовни",
                "aspect_ratio": "3:4"
            }
        )
        el8 = CanvasElement(
            board_id=board2.id,
            element_type="palette",
            x=450,
            y=80,
            width=320,
            height=200,
            z_index=2,
            content={
                "title": "Amber & Espresso Palette",
                "colors": ["#FFF3B0", "#E09F3E", "#9E2A2B", "#540B0E", "#335C67"],
                "tags": ["fashion", "autumn", "vintage"]
            }
        )
        el9 = CanvasElement(
            board_id=board2.id,
            element_type="note",
            x=450,
            y=310,
            width=290,
            height=210,
            z_index=3,
            content={
                "title": "Матеріали та деталі",
                "text": "Натуральна замша, масивні золоті прикраси, структуровані сумки шопери з тисненням.",
                "color": "#F3E8FF",
                "author": "Наталія"
            }
        )
        session.add_all([el7, el8, el9])

        await session.commit()
        logger.info("Seed data successfully committed.")
