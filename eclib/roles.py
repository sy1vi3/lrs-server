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

RW_ = {
    team: (ecapis.chat, ecapis.inspection, ecapis.skills),
    event_partner: (ecapis.chat, ecapis.inspection_ctrl, ecapis.skills_ctrl, ecapis.meeting_ctrl, ecapis.event_ctrl, ecapis.tech_support, ecapis.volunteers, ecapis.team_control, ecapis.event_config),
    referee: (ecapis.chat, ecapis.inspection_ctrl, ecapis.skills_ctrl),
    staff: (ecapis.chat,),
    observer: tuple(),
    livestream: tuple()
}

RO_ = {
    team: (ecapis.skills_scores, ecapis.rankings, ecapis.stats, ecapis.queue , ecapis.settings),
    event_partner: (ecapis.skills_scores, ecapis.rankings, ecapis.stats, ecapis.queue),
    referee: (ecapis.skills_scores, ecapis.rankings, ecapis.stats, ecapis.queue, ecapis.event_room),
    staff: (ecapis.inspection_ctrl, ecapis.skills_ctrl, ecapis.skills_scores, ecapis.rankings, ecapis.stats, ecapis.queue),
    observer: (ecapis.skills_scores, ecapis.rankings, ecapis.stats, ecapis.queue),
    livestream: (ecapis.livestream, ecapis.rankings, ecapis.stats, ecapis.queue)
}

STAFF_ROLES_ = (event_partner, referee, staff)
