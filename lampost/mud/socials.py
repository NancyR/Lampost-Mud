from lampost.comm.broadcast import BroadcastMap
from lampost.context.resource import provides, requires
from lampost.datastore.dbo import RootDBO


SOCIALS =  {"dance": BroadcastMap(s="You gyrate lewdly!",
                    e="{n} gyrates lewdly!",
                    st="You dip {N} in a tango!",
                    et="{n} dips {N} in a tango!",
                    t="{n} dips you in a tango!",
                    sf="You twist yourself in knots tangoing without a partner.",
                    ef="{n} dips ludicrously trying to tango with {F}."),

           "blink": BroadcastMap(s="You blink rapidly in surprise.",
                    e="{n} blinks rapidly in surprise",
                    st="You blink rapidly at {N} in surprise.",
                    et="{n} blinks rapidly at {N} in surprise.",
                    t="{n} blinks rapidly at you in surprise.",
                    sf="You blink at yourself, but see nothing.",
                    ef="{n} blinks in confusion."),

            "spin": BroadcastMap(s="Throwing your arms out to the world and your face up to the sky you spin around and around and around.",
                    e="{n} throws {s} arms out to the world and {s} face to the sky and starts spinning in circles!",
                    st="You catch hold of {n}'s hands in  yours and spin both of you in circles!",
                    et="{n} catches {N}'s hands in {s}, and begins to spin both of them in circles!",
                    t="{n} catches your hands in {s} and spins you both in circles!",
                    sf="Throwing your arms out to the world and your face up to the sky you spin around and around and around. It is grand to be alive!",
                    ef="{n} throws {s} arms out to the world and {s} face to the sky and starts spinning in circles! {e} is enjoying life!",
                    o="Holding onto {N} with both hands, you spin around in circles!",
                    oe="Holding onto {N} with both hands, {n} spins around in circles!"),

            "lgrin": BroadcastMap(s="You manage a lopsided grin. ",
                    e="{n} has a bit of a grin just now.",
                    st="You share a lopsided grin with {N}.",
                    et="{n} shares a lopsided grin with {N}. What's that about? ",
                    t="{n} shares a lopsided grin with you. Presumably you know what it's all about?",
                    sf="While smirking inwardly, you manage a lopsided grin for the world. ",
                    ef="{n}'s grin is just short of being a smirk.",
                    o="You grin lopsidedly at {N}.",
                    oe="{n} grins lopsidedly at {N}."),

            "hop": BroadcastMap(s="You hop around on one foot. Life is good! ",
                    e="{n} hops around on one foot. {e} is happy about something!",
                    st="You catch up {N}'s hand in yours and hop up and down before {M}.",
                    et="{n} catches {N}'s hand in {s} and hops up and down before {M}. Something good must have happened.",
                    t="{n} catches you your hand in {s} then hops up and down before you. Something good must have happened!",
                    sf="You hop twice on your right foot, three times on your left foot, three times on your right foot and 5 times on your left foot.  It's a complicated rhythm but it expresses your feelings exactly.",
                    ef="{n} uses hopping to demonstrate the mating dance of a bee.",
                    o="Holding {N} in your hand, you hop around on one foot.  Life is good! ",
                    oe="Holding {N} in {s} hand, {n} hops around on one foot. {e} is happy about something!" ),

            "nod": BroadcastMap(s="You nod in agreement. ",
                    e="{n} nods in agreement.",
                    st="You nod in agreement with {N}.",
                    et="{n} nods {s} head in agreement with {N}.",
                    t="{n} nods {s} head in agreement with you.",
                    sf="You nod your head thoughtfully.",
                    ef="{n} nods {s} head thoughtfully. Perhaps {e} agrees with {s}self."),

            "dnod": BroadcastMap(s="You nods nods. ",
                    e="{n} nods nods in agreement.",
                    st="You nods nods in agreement with {N}.",
                    et="{n} nods nods in agreement with {N}. {E} is double-sure.",
                    t="{n} nods nods in agreement with you. {E} is double-sure.",
                    sf="You nods nods emphatically. Best to be double-sure",
                    ef="{n} nods nods {s} head emphatically. He is absolutely certain."),

            "bkiss": BroadcastMap(s="You kiss your fingers lightly then blow the kiss softly towards the skies.",
                    e="{n} kisses {s} fingers lightly then blows the kiss to the skies.",
                    st="You kiss your fingers lightly then blow the kiss gently towards {N}!",
                    et="{n} kisses {s} fingers lightly then blow the kiss gently towards {N}!",
                    t="{n} kisses {s} fingers lightly then blows the kiss gently towards you!",
                    sf="You kiss your fingers lightly then gently pat the kiss into your cheek.",
                    ef="{n} kisses {s} fingers lightly then pats the kiss into {s} cheek.",
                    o=" You kiss your fingers lightly then blows the kiss towards {N}.",
                    oe="{n} kisses {s} fingers lightly then blows the kiss towards {N}." )

           }

@provides('social_registry')
@requires('datastore', 'mud_actions')
class SocialRegistry(object):

    def __init__(self):
        self._socials = {}

    def emote(self, source, target, verb, **ignored):
        source.broadcast(broadcast_map=self._socials[verb[0]], target=target)

    def load_socials(self):
        self.mud_actions.add_verb(('socials',), self.socials)
        self.emote.__func__.msg_class = 'rec_social'
        for social_key in self.datastore.fetch_set_keys("socials"):
            social_id = social_key.split(":")[1]
            social = self.datastore.load_object(Social, social_id)
            self.insert(social)

    def insert(self, social):
        self._socials[social.dbo_id] = BroadcastMap(**social.map)
        self.mud_actions.add_verb((social.dbo_id,), self.emote)

    def delete(self, social_verb):
        del self._socials[social_verb]
        self.mud_actions.rem_verb((social_verb,), self.emote)

    def socials(self, **ignored):
        return " ".join(sorted(self._socials.keys()))

    def get(self, social_id):
        return self._socials.get(social_id)


class Social(RootDBO):
    dbo_set_key = 'socials'
    dbo_key_type = 'social'
    dbo_fields = 'map',

    def __init__(self, social_id):
        self.dbo_id = social_id
        self.map = {}



