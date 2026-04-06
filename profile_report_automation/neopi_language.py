from __future__ import annotations

import re
import unicodedata


NEOPI_DOMAIN_ORDER = [
    "Neuroticismo",
    "Extroversão",
    "Abertura",
    "Amabilidade",
    "Conscienciosidade",
]

NEOPI_DISPLAY_LABELS = {
    "Neuroticismo": "Suscetibilidade ao estresse",
    "Extroversão": "Extroversão",
    "Abertura": "Abertura para novidade",
    "Amabilidade": "Amabilidade",
    "Conscienciosidade": "Conscienciosidade",
}

_ARTIFACT_PATTERNS = [
    r"C[ÓO]DIGO DO AVALIADO.*$",
    r"C[ÓO]DIGO DO RELAT[ÓO]RIO.*$",
    r"DATA DA APLICA[ÇC][ÃA]O.*$",
    r"P[aá]g:\s*\d+.*$",
    r"\d+\s*/\s*\d+\s*$",
    r"PROFISSIONAL RESPONS[ÁA]VEL.*$",
    r"NOME DO AVALIADO.*$",
    r"NEO PI-R - Invent[aá]rio de Personalidade NEO Revisado.*$",
    r"Este documento n[aã]o se constitui em um laudo t[eé]cnico.*$",
    r"©\s*20\d{2}.*$",
    r"www\.[^\s]+.*$",
]

_COMMON_REWRITES = [
    (
        r"não transparecendo, na maior parte do tempo, uma imagem apreensiva ou tensa",
        "sem transmitir, na maior parte do tempo, sinais intensos de preocupação ou tensão",
    ),
    (r"\btem controle emocional\b", "apresenta controle emocional"),
    (r"\bnão demonstra\b", "não costuma demonstrar"),
    (
        r"não costuma demonstrar uma postura animada diante de qualquer situação",
        "não costuma demonstrar uma postura empolgada diante de algumas situações",
    ),
    (
        r"podendo até transparecer uma imagem mais reservada em relação às coisas e às situações que acontecem",
        "o que pode transmitir maior seriedade em seu contato",
    ),
    (
        r"reagir com hostilidade ou irritação",
        "responder com irritação ou reações mais intensas",
    ),
    (r"\breações hostis\b", "reações mais contundentes"),
    (r"\breações ríspidas\b", "reações mais diretas"),
    (r"\btransparecer uma imagem apreensiva\b", "transmitir uma imagem de cautela"),
    (r"\btransparecer sua tensão\b", "demonstrar sinais de tensão"),
    (r"\bpostura apreensiva\b", "postura de cautela"),
    (r"\bimagem apreensiva\b", "imagem de cautela"),
    (r"\bimagem apática\b", "imagem mais reservada"),
    (r"\bnão se sensibilizar por\b", "atribuir menor interesse a"),
    (r"\bnão seja resistente em aceitá-las\b", "amplie a abertura para considerá-las"),
    (r"\bmenor preocupação com os princípios éticos e morais\b", "necessidade de reforçar alinhamento com combinados e critérios de decisão"),
    (r"\bmenor apego com suas obrigações e responsabilidades\b", "momento que pode demandar maior atenção à constância nas responsabilidades"),
    (r"\bpouco determinad[oa]\b", "com necessidade de maior constância"),
    (r"\bdespreparo\b", "sensação de menor preparo"),
    (r"\bdespreparad[oa]\b", "menos seguro(a) quanto ao próprio preparo"),
    (r"\bdisplicente\b", "menos atento(a)"),
    (r"\bmedo\b", "receio"),
]

_DOMAIN_REWRITES = {
    "Neuroticismo": [
        (
            r"Atualmente, tende a ter grande preocupação com o futuro e apresenta uma postura de cautela diante de novas perspectivas\.",
            "Atualmente, tende a direcionar elevada atenção ao futuro e a adotar maior cautela diante de novas perspectivas.",
        ),
        (
            r"Concomitantemente, diante de alguma situação que não vá ao encontro de suas expectativas, pode demonstrar sua frustração e também ter reações mais contundentes quanto ao modo de ser ou se comunicar com as demais pessoas\.",
            "Quando situações fogem das expectativas, pode demonstrar frustração e responder de maneira mais contundente na comunicação.",
        ),
        (
            r"Além disso, tende a transmitir uma imagem de cautela e muito preocupada quando em momentos de pressão, podendo não demonstrar a racionalidade habitual ao tomar decisões\.",
            "Em momentos de pressão, pode transmitir maior tensão e demandar mais tempo para organizar decisões com a mesma racionalidade habitual.",
        ),
    ],
    "Extroversão": [
        (
            r"Tende a ser percebido\(a\) como uma pessoa discreta na interação com os outros, pelo fato de manter, na maioria das vezes, uma postura recatada nos contatos interpessoais\.",
            "Tende a ser percebido como uma pessoa discreta na interação com os outros, pelo fato de manter, na maioria das vezes, uma postura recatada nos contatos interpessoais.",
        ),
        (
            r"Além disso, na maioria das vezes, não costuma demonstrar uma postura (?:animada diante de qualquer situação|empolgada diante de algumas situações), podendo até (?:transparecer|transmitir) uma imagem (?:apática|mais reservada) em relação às coisas e às situações que acontecem\.",
            "Além disso, na maioria das vezes, não costuma demonstrar uma postura empolgada diante de algumas situações, transparecendo maior seriedade em seu contato.",
        ),
        (
            r"Assim, corre o risco de se envolver em muitas responsabilidades e tarefas ao mesmo tempo\.",
            "Assim, pode assumir muitas responsabilidades e tarefas ao mesmo tempo.",
        ),
        (
            r"No entanto, pode sentir certo incômodo com períodos nos quais não tenha o que desenvolver e fazer, por preferir estar, na maior parte do tempo, com algum tipo de ocupação\.",
            "Além disso, pode sentir desconforto em períodos com pouca ocupação, por preferir manter-se ativo(a) na maior parte do tempo.",
        ),
    ],
    "Abertura": [
        (
            r"Ao tomar decisões no dia a dia, pode levar menos em consideração os sentimentos, visto que tende a atribuir pouca importância a eles\.",
            "Ao tomar decisões, pode levar menos em consideração os sentimentos, comportando-se de forma mais racional e lógica.",
        ),
        (
            r"Precisa se atentar para que seu apreço por rotinas e desenvolvimentos de tarefas habituais, não leve a uma postura resistente diante de mudanças ou de projetos e atividades novas que não lhe sejam familiares\.",
            "Em contextos de mudança, pode beneficiar-se de tempo para compreender novas propostas e construir familiaridade com elas.",
        ),
        (
            r"Tende a atribuir menor interesse a manifestações artísticas, e tem menor interesse pelas expressões e formas estéticas\.",
            "Tende a atribuir menor interesse a manifestações artísticas e a formas estéticas.",
        ),
        (
            r"Além disso, dispõe de uma gama menor de interesses intelectuais, e um menor grau de curiosidade\.",
            "Além disso, pode concentrar seus interesses intelectuais em um conjunto mais restrito de temas e demonstrar menor curiosidade por assuntos novos.",
        ),
        (
            r"Na maior parte do tempo, não sente atração e interesse por novas ideias ou sugestões, e deve-se atentar para que amplie a abertura para considerá-las\.",
            "Na maior parte do tempo, tende a avaliar novas ideias com maior critério e pode beneficiar-se de ampliar a abertura para considerá-las.",
        ),
    ],
    "Amabilidade": [
        (
            r"Nas atividades do dia a dia, adota uma postura equilibrada entre uma conduta mais autocentrada e uma postura disposta a cooperar com as demais pessoas, ponderando conforme o momento, tendo em vista que se preocupa com o bem-estar alheio, mas não perde o foco das próprias responsabilidades\.",
            "Nas atividades do dia a dia, adota uma postura equilibrada entre atenção às próprias responsabilidades e disposição para cooperar com as demais pessoas, ponderando conforme o momento.",
        ),
        (
            r"Além disso, nas interações sociais não tem dificuldade para confiar na intencionalidade das pessoas de seu convívio, contudo acaba adotando em alguns momentos uma postura mais cética e cautelosa conforme avalia cada contexto\.",
            "Além disso, nas interações sociais não tem dificuldade para confiar nas intenções das pessoas de seu convívio, embora em alguns momentos adote uma postura mais criteriosa e cautelosa conforme avalia cada contexto.",
        ),
    ],
    "Conscienciosidade": [
        (
            r"Tende a não investir muita energia e tempo em buscar informações importantes no preparo para o trabalho e, atualmente, pode se perceber pouco preparado para cumprir as exigências de sua rotina e pouco confiante para tomar decisões\.",
            "Tende a não investir muito tempo em buscar informações no preparo para o trabalho e, atualmente, pode se perceber menos confiante para atender às exigências da rotina e para tomar decisões.",
        ),
        (
            r"Precisa se atentar para que diante de situações emergenciais, a tendência de manter uma postura prudente e a percepção de sensação de menor preparo sobre si mesmo, não postergue sua ação, o que pode influenciar na eficiência de suas atitudes na resolução dos problemas\.",
            "Precisa se atentar para que, diante de situações emergenciais, mantenha uma postura prudente sem adiar a ação, preservando a eficiência na resolução dos problemas.",
        ),
        (
            r"Mantém uma postura com necessidade de maior constância para alcançar as metas e os objetivos estabelecidos e pode ter menos ambição em relação às conquistas e realizações no trabalho, o que não significa que se sinta insatisfeito\(a\) com o que atingiu\.",
            "Pode demonstrar necessidade de maior constância para sustentar metas e objetivos estabelecidos, além de menor ambição em relação a novas conquistas no trabalho, sem que isso signifique insatisfação com o que já alcançou.",
        ),
        (
            r"Neste momento, demonstra momento que pode demandar maior atenção à constância nas responsabilidades e precisa se atentar para que sua necessidade de reforçar alinhamento com combinados e critérios de decisão não interfiram na tomada de decisão, o que pode dificultar o cumprimento de suas responsabilidades conforme esperado\.",
            "Neste momento, pode demandar maior atenção à constância nas responsabilidades, mantendo alinhamento com combinados e critérios de decisão para favorecer o cumprimento do que é esperado.",
        ),
    ],
}


def clean_neopi_synthesis_text(text: str) -> str:
    if not text:
        return ""

    cleaned = unicodedata.normalize("NFC", text).replace("\n", " ").replace("\xa0", " ")
    for pattern in _ARTIFACT_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def rewrite_neopi_synthesis_text(text: str, *, domain_name: str | None = None) -> str:
    rewritten = clean_neopi_synthesis_text(text)
    if not rewritten:
        return ""

    for pattern, replacement in _COMMON_REWRITES:
        rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)

    for pattern, replacement in _DOMAIN_REWRITES.get(domain_name or "", []):
        rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)

    rewritten = re.sub(r"\(\s*a\s*\)", "", rewritten, flags=re.IGNORECASE)
    rewritten = re.sub(r"\s+([,.;:])", r"\1", rewritten)
    rewritten = re.sub(r"\s+", " ", rewritten).strip()
    if rewritten and rewritten[-1] not in ".!?":
        rewritten = f"{rewritten}."
    return rewritten


def build_friendly_neopi_synthesis_map(synthesis_by_domain: dict[str, str]) -> dict[str, str]:
    rewritten_map: dict[str, str] = {}
    for domain_name, text in synthesis_by_domain.items():
        rewritten = rewrite_neopi_synthesis_text(text, domain_name=domain_name)
        if rewritten:
            rewritten_map[domain_name] = rewritten
    return rewritten_map
