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
    event_partner: (ecapis.chat, ecapis.inspection_ctrl, ecapis.skills_ctrl, ecapis.meeting_ctrl, ecapis.event_ctrl, ecapis.tech_support),
    referee: (ecapis.chat, ecapis.inspection_ctrl, ecapis.skills_ctrl),
    staff: (ecapis.chat,),
    observer: tuple(),
    livestream: tuple()
}

RO_ = {
    team: (ecapis.skills_scores, ecapis.rankings),
    event_partner: (ecapis.skills_scores, ecapis.rankings),
    referee: (ecapis.skills_scores, ecapis.rankings),
    staff: (ecapis.inspection_ctrl, ecapis.skills_ctrl, ecapis.skills_scores, ecapis.rankings),
    observer: (ecapis.chat, ecapis.inspection_ctrl, ecapis.skills_ctrl, ecapis.skills_scores, ecapis.rankings),
    livestream: (ecapis.livestream, ecapis.rankings)
}

STAFF_ROLES_ = (event_partner, referee, staff)
