# PROTO_FIELD_MAP: Maps protobuf field IDs to semantic names
# (Based on community-documented field mappings for Garena's wire protocol)

PROTO_FIELD_MAP = {
    # Request Fields
    "request": {
        1: "uid",
        2: "region",
        3: "version",
    },

    # Response Fields (Account Info)
    "response": {
        1: "account_info",
        2: "rank_info",
        3: "stats_info",
        4: "social_info",
        5: "pet_info",
        6: "cosmetics_info",
        7: "pass_info",
        8: "credit_info",
        9: "ban_info",
    },

    # Nested Maps (Field Name -> Map Key)
    "nested_mapping": {
        "account_info": "account",
        "rank_info": "rank",
        "br_rank": "br_rank",
        "cs_rank": "cs_rank",
        "stats_info": "stats",
        "br_stats": "br_stats",
        "cs_stats": "cs_stats_map",
        "solo": "stat_line",
        "duo": "stat_line",
        "squad": "stat_line",
        "social_info": "social",
        "guild": "guild",
        "leader": "guild_leader",
        "pet_info": "pet",
        "cosmetics_info": "cosmetics",
        "pass_info": "pass",
        "credit_info": "credit",
        "ban_info": "ban",
    },

    # Nested Account Info
    "account": {
        1: "uid",
        2: "nickname",
        3: "level",
        4: "exp",
        5: "region",
        6: "season_id",
        7: "preferred_mode",
        8: "language",
        9: "signature",
        10: "honor_score",
        11: "total_likes",
        12: "ob_version",
        13: "created_at_epoch",
        14: "last_login_epoch",
        15: "account_type",
    },

    # Nested Rank Info
    "rank": {
        1: "br_rank",
        2: "cs_rank",
    },
    "br_rank": {
        1: "rank_code",
        2: "points",
        3: "max_rank_code",
        4: "visible",
    },
    "cs_rank": {
        1: "rank_code",
        2: "points",
        3: "visible",
    },

    # Nested Stats Info
    "stats": {
        1: "br_stats",
        2: "cs_stats",
    },
    "cs_stats_map": {
        1: "ranked",
    },
    "br_stats": {
        1: "solo",
        2: "duo",
        3: "squad",
    },
    "stat_line": {
        1: "matches",
        2: "wins",
        3: "kills",
        4: "deaths",
        5: "headshots",
        6: "avg_damage",
    },

    # Nested Social Info
    "social": {
        1: "guild",
    },
    "guild": {
        1: "id",
        2: "name",
        3: "level",
        4: "member_count",
        5: "capacity",
        6: "leader",
    },
    "guild_leader": {
        1: "uid",
        2: "nickname",
        3: "level",
        4: "rank_code",
    },

    # Nested Pet Info
    "pet": {
        1: "name",
        2: "level",
        3: "exp",
        4: "active_skill",
        5: "skin_id",
        6: "is_selected",
    },

    # Nested Cosmetics
    "cosmetics": {
        1: "avatar_id",
        2: "banner_id",
        3: "pin_id",
        4: "character_id",
        5: "outfit_ids",
        6: "weapon_skin_ids",
    },

    # Nested Pass Info
    "pass": {
        1: "booyah_pass_level",
        2: "fire_pass_status",
        3: "fire_pass_badge_count",
    },

    # Nested Credit Info
    "credit": {
        1: "score",
        2: "reward_claimed",
        3: "summary_period",
    },

    # Nested Ban Info
    "ban": {
        1: "is_banned",
        2: "ban_period",
        3: "ban_type",
    }
}
