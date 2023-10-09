"""
Names and permissions of Event Console user roles
"""
import eclib.apis as ecapis

team = "Team"
event_partner = "Event Partner"
referee = "Head Referee"
staff = "Staff"
observer = "Observer"
livestream = "Livestream"
output = "Output"
producer = "Producer"

RW_ = {
    team: (ecapis.chat, ecapis.inspection, ecapis.skills, ecapis.settings),
    event_partner: (ecapis.chat, ecapis.inspection_ctrl, ecapis.skills_ctrl, ecapis.meeting_ctrl, ecapis.event_ctrl, ecapis.tech_support, ecapis.volunteers, ecapis.team_control, ecapis.event_config, ecapis.production, ecapis.home, ecapis.jwt, ecapis.moderation, ecapis.jwt),
    referee: (ecapis.chat, ecapis.inspection_ctrl, ecapis.skills_ctrl, ecapis.jwt, ecapis.moderation, ecapis.meeting_ctrl),
    staff: (ecapis.chat, ecapis.home, ecapis.jwt, ecapis.moderation, ecapis.jwt, ecapis.meeting_ctrl),
    observer: tuple(),
    livestream: (ecapis.jwt,),
    output: tuple(),
    producer: (ecapis.chat, ecapis.production, ecapis.output, ecapis.moderation, ecapis.jwt, ecapis.meeting_ctrl)
}

RO_ = {
    team: (ecapis.home, ecapis.skills_scores, ecapis.rankings, ecapis.stats, ecapis.queue, ecapis.help),
    event_partner: (ecapis.skills_scores, ecapis.rankings, ecapis.stats, ecapis.queue, ecapis.help),
    referee: (ecapis.skills_scores, ecapis.rankings, ecapis.stats, ecapis.queue, ecapis.event_room, ecapis.home, ecapis.help),
    staff: (ecapis.inspection_ctrl, ecapis.skills_ctrl, ecapis.skills_scores, ecapis.rankings, ecapis.stats, ecapis.queue, ecapis.help),
    observer: (ecapis.skills_scores, ecapis.rankings, ecapis.stats, ecapis.queue, ecapis.home, ecapis.help, ecapis.chat),
    livestream: (ecapis.livestream, ecapis.rankings, ecapis.stats, ecapis.queue),
    output: (ecapis.livestream, ecapis.rankings, ecapis.stats, ecapis.queue, ecapis.output),
    producer: (ecapis.skills_scores, ecapis.rankings, ecapis.stats, ecapis.queue, ecapis.home, ecapis.help)
}

STAFF_ROLES_ = (event_partner, referee, staff, producer)
