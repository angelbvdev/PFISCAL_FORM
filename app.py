from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from math import cos, pi, sin
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Dict, List, Tuple

from flask import Flask, redirect, render_template, request, session, url_for


def _load_dotenv(path: str = ".env") -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return

    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        key, value = s.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        os.environ.setdefault(key, value)

    # Conveniencia: permitir APP_DEBUG en lugar de FLASK_DEBUG.
    if "APP_DEBUG" in os.environ and "FLASK_DEBUG" not in os.environ:
        os.environ["FLASK_DEBUG"] = os.environ["APP_DEBUG"]


def _env_flag(name: str) -> bool | None:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return None
    val = raw.strip().lower()
    if val in {"1", "true", "yes", "y", "on"}:
        return True
    if val in {"0", "false", "no", "n", "off"}:
        return False
    return None


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    text: str


QUESTIONS: List[Question] = [
    Question(
        id="q01",
        category="Dirección y Estrategia",
        text="La empresa cuenta con una misión, visión y valores definidos, y la dirección los tiene claros.",
    ),
    Question(
        id="q02",
        category="Dirección y Estrategia",
        text="Existe una estrategia definida (a qué clientes se dirige, qué ofrece y cómo se diferencia de la competencia).",
    ),
    Question(
        id="q03",
        category="Dirección y Estrategia",
        text="Se establecen objetivos anuales y metas medibles, y la dirección los utiliza como base para gestionar el negocio.",
    ),
    Question(
        id="q04",
        category="Dirección y Estrategia",
        text="Se realiza un seguimiento periódico al cumplimiento de los objetivos y se toman decisiones para corregir desviaciones.",
    ),
    Question(
        id="q05",
        category="Dirección y Estrategia",
        text="La operación diaria está lo suficientemente delegada y el negocio no depende exclusivamente del dueño o de una sola persona clave.",
    ),
    Question(
        id="q06",
        category="Finanzas",
        text="La empresa cuenta con registros contables ordenados y elabora reportes mensuales básicos (estado de resultados y flujo de efectivo).",
    ),
    Question(
        id="q07",
        category="Finanzas",
        text="Se conoce con claridad el costo de los productos o servicios, incluyendo mano de obra, materiales y gastos indirectos.",
    ),
    Question(
        id="q08",
        category="Finanzas",
        text="Se monitorea la rentabilidad del negocio (márgenes, utilidad) y se usan estos datos para tomar decisiones.",
    ),
    Question(
        id="q09",
        category="Finanzas",
        text="Se gestiona el flujo de efectivo de forma anticipada (proyección de ingresos y egresos, planeación de pagos y cobros).",
    ),
    Question(
        id="q10",
        category="Finanzas",
        text="Existe un presupuesto o control de gastos y se revisa periódicamente para evitar desviaciones importantes.",
    ),
    Question(
        id="q11",
        category="Operaciones / Procesos",
        text="Los procesos clave del negocio (venta, servicio, producción, administración, atención a clientes, etc.) están identificados y descritos.",
    ),
    Question(
        id="q12",
        category="Operaciones / Procesos",
        text="Existen estándares de trabajo (pasos claros, tiempos, checklists) que guían cómo debe hacerse cada proceso importante.",
    ),
    Question(
        id="q13",
        category="Operaciones / Procesos",
        text="Se miden indicadores operativos básicos (tiempos de respuesta, retrabajos, incumplimientos) y se registran de manera consistente.",
    ),
    Question(
        id="q14",
        category="Operaciones / Procesos",
        text="Las herramientas y sistemas utilizados (software, formatos, procesos) apoyan adecuadamente la operación y no generan retrabajo innecesario.",
    ),
    Question(
        id="q15",
        category="Operaciones / Procesos",
        text="Se realizan mejoras periódicas en los procesos a partir de problemas detectados, datos o sugerencias del equipo (no solo cuando hay crisis).",
    ),
    Question(
        id="q16",
        category="Comercial (Ventas / Marketing)",
        text="Los procesos clave del negocio (venta, servicio, producción, administración, atención a clientes, etc.) están identificados y descritos.",
    ),
    Question(
        id="q17",
        category="Comercial (Ventas / Marketing)",
        text="Existen estándares de trabajo (pasos claros, tiempos, checklists) que guían cómo debe hacerse cada proceso importante.",
    ),
    Question(
        id="q18",
        category="Comercial (Ventas / Marketing)",
        text="Se miden indicadores operativos básicos (tiempos de respuesta, errores, retrabajos, incumplimientos) y se registran de manera consistente.",
    ),
    Question(
        id="q19",
        category="Comercial (Ventas / Marketing)",
        text="Las herramientas y sistemas utilizados (software, formatos, plantillas) soportan adecuadamente la operación y no generan retrabajo innecesario.",
    ),
    Question(
        id="q20",
        category="Comercial (Ventas / Marketing)",
        text="Se realizan mejoras periódicas en los procesos a partir de problemas detectados, datos o sugerencias del equipo (no solo cuando hay crisis).",
    ),
    Question(
        id="q21",
        category="RH (Personas y Cultura)",
        text="Existe una estructura organizacional clara (organigrama) y las personas saben a quién reportan y cuáles son sus responsabilidades.",
    ),
    Question(
        id="q22",
        category="RH (Personas y Cultura)",
        text="Se cuenta con descripciones de puesto para los roles clave, incluyendo funciones y responsabilidades principales.",
    ),
    Question(
        id="q23",
        category="RH (Personas y Cultura)",
        text="Existe un proceso definido de reclutamiento e inducción para las nuevas personas que ingresan a la empresa.",
    ),
    Question(
        id="q24",
        category="RH (Personas y Cultura)",
        text="Se realiza algún tipo de evaluación de desempeño o retroalimentación formal al personal, al menos una vez al año.",
    ),
    Question(
        id="q25",
        category="RH (Personas y Cultura)",
        text="El clima laboral (comunicación, respeto, colaboración) se percibe en general como positivo y favorece el compromiso con la empresa.",
    ),
]

SCALE: List[Tuple[int, str]] = [
    (1, "No"),
    (2, "Más no que sí"),
    (3, "Parcial"),
    (4, "Más sí que no"),
    (5, "Sí"),
]


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    debug_flag = _env_flag("FLASK_DEBUG")
    if debug_flag is not None:
        app.config["DEBUG"] = debug_flag
    app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
    app.config["OPENAI_MODEL"] = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    app.config["OPENAI_BASE_URL"] = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    app.config["OPENAI_TIMEOUT_SECONDS"] = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "10"))
    app.config["OPENAI_API_MODE"] = os.getenv("OPENAI_API_MODE", "auto").strip().lower() or "auto"

    @app.get("/")
    def index():
        return render_template("welcome.html")

    @app.get("/cuestionario")
    def cuestionario():
        last_answers = session.get("last_answers", {})
        return render_template(
            "quiz.html",
            questions=QUESTIONS,
            scale=SCALE,
            last_answers=last_answers,
        )

    @app.post("/resultado")
    def resultado():
        answers = _parse_answers(request.form)
        if isinstance(answers, str):
            session["flash_error"] = answers
            return redirect(url_for("cuestionario"))

        session["last_answers"] = answers
        total, total_pct, by_category = _compute_scores(answers)
        radar = _build_radar(by_category)
        ai, ai_error, ai_error_detail = _maybe_ai_result(
            api_key=app.config["OPENAI_API_KEY"],
            base_url=app.config["OPENAI_BASE_URL"],
            model=app.config["OPENAI_MODEL"],
            api_mode=app.config["OPENAI_API_MODE"],
            timeout_seconds=app.config["OPENAI_TIMEOUT_SECONDS"],
            total_pct=total_pct,
            by_category=by_category,
            answers=answers,
            debug=bool(app.debug),
        )

        return render_template(
            "result.html",
            questions=QUESTIONS,
            answers=answers,
            total=total,
            total_pct=total_pct,
            by_category=by_category,
            radar=radar,
            ai=ai,
            ai_error=ai_error,
            ai_error_detail=ai_error_detail,
            ai_enabled=bool(app.config["OPENAI_API_KEY"]),
            interpretation=_interpretation(
                total_pct,
                by_category=by_category,
                api_key=app.config["OPENAI_API_KEY"],
                base_url=app.config["OPENAI_BASE_URL"],
                model=app.config["OPENAI_MODEL"],
                api_mode=app.config["OPENAI_API_MODE"],
                timeout_seconds=app.config["OPENAI_TIMEOUT_SECONDS"],
                debug=bool(app.debug),
            ),
        )

    @app.get("/reset")
    def reset():
        session.pop("last_answers", None)
        session.pop("flash_error", None)
        return redirect(url_for("index"))

    @app.context_processor
    def inject_flash_error():
        flash_error = session.pop("flash_error", None)
        return {"flash_error": flash_error}

    return app


def _parse_answers(form) -> Dict[str, int] | str:
    answers: Dict[str, int] = {}
    for q in QUESTIONS:
        raw = form.get(q.id)
        if raw is None:
            return "Faltan respuestas: contesta todas las preguntas antes de continuar."
        try:
            value = int(raw)
        except ValueError:
            return "Respuestas inválidas: vuelve a intentarlo."
        if value not in {1, 2, 3, 4, 5}:
            return "Respuestas fuera de rango: vuelve a intentarlo."
        answers[q.id] = value
    return answers


def _compute_scores(answers: Dict[str, int]) -> Tuple[int, int, Dict[str, Dict[str, int]]]:
    values = list(answers.values())
    total_points = sum(values)  # 20..100
    total_pct = round((total_points / (len(values) * 5)) * 100)

    by_category: Dict[str, List[int]] = {}
    for q in QUESTIONS:
        by_category.setdefault(q.category, []).append(answers[q.id])

    by_category_summary: Dict[str, Dict[str, int]] = {}
    for category, nums in by_category.items():
        points = sum(nums)
        pct = round((points / (len(nums) * 5)) * 100)
        by_category_summary[category] = {"points": points, "pct": pct, "max": len(nums) * 5}

    return total_points, total_pct, by_category_summary


def _interpretation_level(total_pct: int) -> str:
    if total_pct >= 80:
        return "Alto"
    if total_pct >= 60:
        return "Medio"
    return "Bajo"


def _interpretation_static(total_pct: int) -> Dict[str, str]:
    level = _interpretation_level(total_pct)
    if level == "Alto":
        message = (
            "Tu empresa muestra bases sólidas. Prioriza mantener disciplina de seguimiento y mejorar con datos."
        )
    elif level == "Medio":
        message = (
            "Hay avances, pero existen brechas. Enfócate en 2–3 áreas con menor puntaje para crear un plan trimestral."
        )
    else:
        message = "Hay oportunidades importantes. Empieza por clarificar estrategia, ordenar finanzas y definir procesos mínimos."
    return {"level": level, "message": message}


def _interpretation(
    total_pct: int,
    *,
    by_category: Dict[str, Dict[str, int]] | None = None,
    api_key: str,
    base_url: str,
    model: str,
    api_mode: str,
    timeout_seconds: int,
    debug: bool,
) -> Dict[str, str]:
    static = _interpretation_static(total_pct)
    if not api_key:
        return static

    by_category = by_category or {}
    try:
        msg, err = _maybe_ai_interpretation_message(
            api_key=api_key,
            base_url=base_url,
            model=model,
            api_mode=api_mode,
            timeout_seconds=timeout_seconds,
            total_pct=total_pct,
            level=static["level"],
            by_category=by_category,
        )
    except Exception as e:
        if debug:
            session["flash_error"] = f"No se pudo generar interpretación con IA ({type(e).__name__})."
        return static

    if msg:
        return {"level": static["level"], "message": msg}
    if err and debug:
        session["flash_error"] = f"No se pudo generar interpretación con IA ({err})."
    return static


def _maybe_ai_interpretation_message(
    *,
    api_key: str,
    base_url: str,
    model: str,
    api_mode: str,
    timeout_seconds: int,
    total_pct: int,
    level: str,
    by_category: Dict[str, Dict[str, int]],
) -> Tuple[str | None, str | None]:
    payload = {
        "total_pct": int(total_pct),
        "level": str(level),
        "by_category": {k: {"pct": int(v.get("pct", 0))} for k, v in by_category.items()},
    }

    cache_key = f"ai_interp_v1:{_stable_hash(payload)}"
    cached = session.get(cache_key)
    if isinstance(cached, str) and cached.strip():
        return cached.strip(), None

    system = (
        "Eres un consultor de Consilium. "
        "Escribes interpretaciones ejecutivas breves, claras y accionables. "
        "Responde en español. No inventes datos."
    )
    user = (
        "Genera una interpretación ejecutiva (1–2 frases) del prediagnóstico. "
        "Debe sonar consultiva y concreta, sin alarmismo, sin promesas, y sin pasos. "
        "No menciones 'IA'.\n\n"
        "Devuelve SOLO un JSON válido (sin markdown) con esta forma exacta:\n"
        '{ "message": string }\n\n'
        "Contexto:\n"
        f"- Índice global: {int(total_pct)}%\n"
        f"- Nivel: {level}\n"
        f"- Porcentaje por área (si existe): {json.dumps(payload['by_category'], ensure_ascii=False)}\n"
    )

    raw_text, err = _openai_text(
        api_key=api_key,
        base_url=base_url,
        model=model,
        api_mode=api_mode,
        system=system,
        user=user,
        timeout_seconds=timeout_seconds,
    )
    if not raw_text:
        return None, (err or "Sin contenido de salida desde OpenAI.")

    parsed = _extract_json_object(raw_text)
    if not isinstance(parsed, dict):
        return None, "No se pudo parsear JSON desde la respuesta del modelo."

    msg = parsed.get("message")
    msg = msg.strip() if isinstance(msg, str) else ""
    if not msg:
        return None, "La respuesta JSON no incluye 'message'."

    session[cache_key] = msg
    return msg, None


def _maybe_ai_result(
    *,
    api_key: str,
    base_url: str,
    model: str,
    api_mode: str,
    timeout_seconds: int,
    total_pct: int,
    by_category: Dict[str, Dict[str, int]],
    answers: Dict[str, int],
    debug: bool,
) -> Tuple[Dict[str, object] | None, str | None, str | None]:
    if not api_key:
        return None, None, None

    categories_ranked = sorted(
        (
            {
                "category": k,
                "points": int(v["points"]),
                "pct": int(v["pct"]),
                "max": int(v["max"]),
            }
            for k, v in by_category.items()
        ),
        key=lambda x: x["pct"],
    )

    questions_payload: List[Dict[str, object]] = []
    for q in QUESTIONS:
        questions_payload.append(
            {
                "id": q.id,
                "category": q.category,
                "text": q.text,
                "value": int(answers.get(q.id, 0)),
            }
        )
    weakest_questions_full = sorted(questions_payload, key=lambda x: x["value"])[:5]
    strongest_questions_full = sorted(questions_payload, key=lambda x: x["value"], reverse=True)[:5]

    def drop_value(items: List[Dict[str, object]]) -> List[Dict[str, object]]:
        out: List[Dict[str, object]] = []
        for it in items:
            out.append({"id": it.get("id", ""), "category": it.get("category", ""), "text": it.get("text", "")})
        return out

    weakest_questions = drop_value(weakest_questions_full)
    strongest_questions = drop_value(strongest_questions_full)

    payload = {
        "brand": {
            "company": "Consilium",
            "service": "Consilium",
            "positioning": (
                "Acompañamiento contable y fiscal para dueños de PyMEs: orden, cumplimiento y claridad para decidir."
            ),
        },
        "total_pct": total_pct,
        "interpretation": _interpretation_static(total_pct),
        "by_category": {
            k: {"points": int(v["points"]), "pct": int(v["pct"]), "max": int(v["max"])}
            for k, v in by_category.items()
        },
        "categories_ranked_low_to_high": categories_ranked,
        "weakest_areas": categories_ranked[:2],
        "strongest_areas": sorted(categories_ranked, key=lambda x: x["pct"], reverse=True)[:2],
        "questions": {
            "weakest_5": weakest_questions,
            "strongest_5": strongest_questions,
        },
        "category_definitions": {
            "Dirección y Estrategia": "Claridad de rumbo, objetivos, seguimiento y delegación.",
            "Finanzas": "Contabilidad al día, costos, márgenes, flujo de efectivo, presupuesto y control.",
            "Operaciones / Procesos": "Procesos definidos, estándares, medición e iniciativas de mejora.",
            "Comercial (Ventas / Marketing)": "Prospección, conversión, seguimiento y consistencia comercial.",
            "RH (Personas y Cultura)": "Roles claros, contratación/inducción, desempeño y clima.",
        },
        "scale": {
            "min": 1,
            "max": 5,
            "labels": [{"value": v, "label": lbl} for v, lbl in SCALE],
            "questions_per_area": 5,
            "max_points_per_area": 25,
        },
        "areas_expected": [
            "Dirección y Estrategia",
            "Finanzas",
            "Operaciones / Procesos",
            "Comercial (Ventas / Marketing)",
            "RH (Personas y Cultura)",
        ],
    }

    cache_key = f"ai_v5:{_stable_hash(payload)}"
    cached = session.get(cache_key)
    if isinstance(cached, dict):
        return cached, None, None

    try:
        ai, err = _generate_ai_insights(
            api_key=api_key,
            base_url=base_url,
            model=model,
            api_mode=api_mode,
            timeout_seconds=timeout_seconds,
            scoring_payload=payload,
        )
    except Exception as e:
        public = "No se pudo generar el plan con IA. Verifica tu configuración e inténtalo de nuevo."
        detail = f"{type(e).__name__}: {e}"
        return None, public, (detail if debug else None)

    if ai is not None:
        session[cache_key] = ai
    if err:
        public = "No se pudo generar el plan con IA en este momento."
        return None, public, (err if debug else None)
    return ai, None, None


def _generate_ai_insights(
    *,
    api_key: str,
    base_url: str,
    model: str,
    api_mode: str,
    timeout_seconds: int,
    scoring_payload: Dict[str, object],
) -> Tuple[Dict[str, object] | None, str | None]:
    system = (
        "Eres un consultor de mejora empresarial y ventas consultivas de Consilium. "
        "Tu prioridad es ser específico: decir qué falta, dónde está el riesgo y cómo lo resolvemos. "
        "Responde en español, con empatía y claridad, basado SOLO en el scoring. "
        "No inventes datos. No prometas resultados garantizados. No uses lenguaje legal."
    )
    user = (
        "Con base en este prediagnóstico, enfócate en vender el servicio: "
        "nombra el dolor (lo que más les está doliendo), el problema principal (brecha más crítica), "
        "y cómo Consilium los ayuda. NO des un plan de acción todavía.\n\n"
        "Devuelve SOLO un JSON válido (sin markdown) con esta forma exacta:\n"
        "{\n"
        '  "titulo": string,\n'
        '  "diagnostico_en_una_frase": string,\n'
        '  "problema_principal": string,\n'
        '  "lo_que_te_esta_doliendo": string,\n'
        '  "como_ayudamos_consilium": string,\n'
        '  "que_incluye_consilium": [string, string, string],\n'
        '  "beneficios_para_ti": [string, string, string]\n'
        "}\n"
        "Reglas:\n"
        "- Máximo 1–2 frases por campo string.\n"
        "- Máximo 1 frase por item en listas.\n"
        "- Usa un tono cercano y consultivo (que suene a que entendemos su dolor y el costo del desorden).\n"
        "- Prioriza las 2 áreas con menor % para describir el problema.\n"
        "- Si hay empate, prioriza Finanzas y Operaciones.\n"
        "- NO incluyas puntajes 1–5 ni anotaciones tipo \"(1)\"; solo porcentajes (%).\n"
        "- NO incluyas pasos, cronogramas, ni planes de 30/90 días.\n"
        "- NO uses markdown.\n\n"
        "Hazlo preciso (obligatorio):\n"
        '- En "problema_principal", menciona explícitamente las 2 áreas más bajas con su % y 1–2 de las preguntas más bajas (usa su texto tal cual o muy cercano).\n'
        '- En "lo_que_te_esta_doliendo", describe 2 consecuencias concretas de esas brechas (ej.: decisiones a ciegas, fugas de efectivo, estrés por cierres/obligaciones, riesgo de recargos), sin alarmismo.\n'
        '- En "como_ayudamos_consilium", conecta directamente esas brechas con 2–3 acciones/entregables concretos (ej.: contabilidad al día y conciliaciones; calendario de obligaciones; reportes mensuales de resultados/flujo; controles mínimos de facturación/gastos). No uses palabras genéricas como "optimizar" o "mejorar" sin explicar qué entregamos.\n'
        '- En "que_incluye_consilium", lista 3 entregables específicos (no conceptos abstractos).\n\n'
        "Qué vende Consilium (ajusta al scoring):\n"
        "- Orden contable y fiscal + cumplimiento.\n"
        "- Reportes claros (estado de resultados, flujo, indicadores) para decidir.\n"
        "- Controles y procesos mínimos para que el negocio no dependa del caos.\n\n"
        "Cómo interpretar el scoring:\n"
        "- Las áreas y preguntas más bajas representan fricción, riesgo y decisiones a ciegas.\n"
        "- Conecta el problema con consecuencias reales (estrés, falta de control, multas/recargos, fugas de efectivo) sin alarmismo.\n\n"
        f"SCORING:\n{json.dumps(scoring_payload, ensure_ascii=False)}"
    )

    raw_text, err = _openai_text(
        api_key=api_key,
        base_url=base_url,
        model=model,
        api_mode=api_mode,
        system=system,
        user=user,
        timeout_seconds=timeout_seconds,
    )
    if not raw_text:
        return None, (err or "Sin contenido de salida desde OpenAI.")

    parsed = _extract_json_object(raw_text)
    if parsed is None:
        return None, "No se pudo parsear JSON desde la respuesta del modelo."

    normalized = _normalize_ai_output(parsed)
    if normalized is None:
        return None, "La respuesta JSON no cumple el formato esperado."
    return normalized, None


def _openai_text(
    *,
    api_key: str,
    base_url: str,
    model: str,
    api_mode: str,
    system: str,
    user: str,
    timeout_seconds: int,
) -> Tuple[str | None, str | None]:
    mode = (api_mode or "auto").strip().lower()
    if mode not in {"auto", "responses", "chat_completions"}:
        mode = "auto"

    if mode in {"auto", "responses"}:
        text, err = _openai_responses_text(
            api_key=api_key,
            base_url=base_url,
            model=model,
            system=system,
            user=user,
            timeout_seconds=timeout_seconds,
        )
        if text:
            return text, None
        if mode == "responses" or not _should_fallback_to_chat(err):
            return None, err

    return _openai_chat_completions_text(
        api_key=api_key,
        base_url=base_url,
        model=model,
        system=system,
        user=user,
        timeout_seconds=timeout_seconds,
    )


def _should_fallback_to_chat(err: str | None) -> bool:
    if not err:
        return False
    s = err.lower()
    return any(
        token in s
        for token in {
            "http 400",
            "http 404",
            "http 405",
            "invalid value",
            "not found",
            "unknown route",
            "unrecognized request",
            "/responses",
        }
    )


def _openai_responses_text(
    *,
    api_key: str,
    base_url: str,
    model: str,
    system: str,
    user: str,
    timeout_seconds: int,
) -> Tuple[str | None, str | None]:
    url = base_url.rstrip("/") + "/responses"
    body = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system}]},
            {"role": "user", "content": [{"type": "input_text", "text": user}]},
        ],
        "temperature": 0.3,
    }
    data = json.dumps(body).encode("utf-8")
    req = Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=data,
    )
    try:
        with urlopen(req, timeout=timeout_seconds) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        try:
            details = e.read().decode("utf-8", errors="replace")
        except Exception:
            details = ""
        details = details.strip()
        if len(details) > 600:
            details = details[:600] + "…"
        return None, f"HTTP {getattr(e, 'code', '?')} desde OpenAI. {details}"
    except (URLError, TimeoutError) as e:
        return None, f"Error de red/timeout hacia OpenAI: {e}"
    except ValueError as e:
        return None, f"Respuesta inválida (no JSON) desde OpenAI: {e}"

    # Responses API: collect text chunks from output content items.
    output = payload.get("output", [])
    texts: List[str] = []
    for item in output:
        for content in item.get("content", []) or []:
            if isinstance(content, dict) and content.get("type") == "output_text":
                t = content.get("text")
                if isinstance(t, str) and t.strip():
                    texts.append(t)
    final = "\n".join(texts).strip() if texts else None
    return final, None


def _openai_chat_completions_text(
    *,
    api_key: str,
    base_url: str,
    model: str,
    system: str,
    user: str,
    timeout_seconds: int,
) -> Tuple[str | None, str | None]:
    url = base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
    }
    data = json.dumps(body).encode("utf-8")
    req = Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=data,
    )
    try:
        with urlopen(req, timeout=timeout_seconds) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        try:
            details = e.read().decode("utf-8", errors="replace")
        except Exception:
            details = ""
        details = details.strip()
        if len(details) > 600:
            details = details[:600] + "…"
        return None, f"HTTP {getattr(e, 'code', '?')} desde OpenAI. {details}"
    except (URLError, TimeoutError) as e:
        return None, f"Error de red/timeout hacia OpenAI: {e}"
    except ValueError as e:
        return None, f"Respuesta inválida (no JSON) desde OpenAI: {e}"

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None, "Respuesta inesperada desde OpenAI (sin choices)."
    msg = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = msg.get("content") if isinstance(msg, dict) else None
    if not isinstance(content, str) or not content.strip():
        return None, "Respuesta inesperada desde OpenAI (sin contenido)."
    return content.strip(), None


def _extract_json_object(text: str) -> Dict[str, object] | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    # Try direct parse first.
    try:
        val = json.loads(cleaned)
        return val if isinstance(val, dict) else None
    except ValueError:
        pass

    # Fallback: extract first balanced JSON object.
    start = cleaned.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(cleaned)):
        ch = cleaned[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = cleaned[start : i + 1]
                try:
                    val = json.loads(candidate)
                    return val if isinstance(val, dict) else None
                except ValueError:
                    return None
        elif depth == 0 and ch.strip():
            # Non-whitespace before object close: keep scanning from the first '{' anyway.
            continue

    return None


def _normalize_ai_output(obj: Dict[str, object]) -> Dict[str, object] | None:
    required = [
        "titulo",
        "diagnostico_en_una_frase",
        "problema_principal",
        "lo_que_te_esta_doliendo",
        "como_ayudamos_consilium",
        "que_incluye_consilium",
        "beneficios_para_ti",
    ]
    if any(k not in obj for k in required):
        return None

    def as_str(v) -> str:
        return v.strip() if isinstance(v, str) else ""

    def as_list(v) -> List[str]:
        if not isinstance(v, list):
            return []
        out: List[str] = []
        for item in v:
            s = as_str(item)
            if s:
                out.append(s)
        return out[:3]

    normalized = {
        "titulo": as_str(obj.get("titulo")),
        "diagnostico_en_una_frase": as_str(obj.get("diagnostico_en_una_frase")),
        "problema_principal": as_str(obj.get("problema_principal")),
        "lo_que_te_esta_doliendo": as_str(obj.get("lo_que_te_esta_doliendo")),
        "como_ayudamos_consilium": as_str(obj.get("como_ayudamos_consilium")),
        "que_incluye_consilium": as_list(obj.get("que_incluye_consilium")),
        "beneficios_para_ti": as_list(obj.get("beneficios_para_ti")),
        "meta": {"model": str(obj.get("model", ""))[:64], "ts": int(time.time())},
    }
    if (
        not normalized["titulo"]
        or not normalized["diagnostico_en_una_frase"]
        or not normalized["problema_principal"]
        or not normalized["lo_que_te_esta_doliendo"]
        or not normalized["como_ayudamos_consilium"]
        or not normalized["que_incluye_consilium"]
        or not normalized["beneficios_para_ti"]
    ):
        return None
    return normalized


def _stable_hash(obj: object) -> str:
    # Stable, non-crypto hash for cache keys.
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return hex(h)[2:]


def _build_radar(by_category: Dict[str, Dict[str, int]]) -> Dict[str, object]:
    axes = [
        ("Dirección y Estrategia", "Dirección y Estrategia"),
        ("Finanzas", "Finanzas"),
        ("Operaciones / Procesos", "Operaciones / Procesos"),
        ("Comercial (Ventas / Marketing)", "Comercial (Ventas / Marketing)"),
        ("RH (Personas y Cultura)", "RH (Personas y Cultura)"),
    ]

    max_points = 25
    values: List[Dict[str, object]] = []
    for axis_label, internal_category in axes:
        data = by_category.get(internal_category)
        points = int(data["points"]) if data else 0
        pct = int(data["pct"]) if data else 0
        values.append(
            {
                "label": axis_label,
                "category": internal_category,
                "points": points,
                "pct": pct,
                "max": max_points,
            }
        )

    size = 340
    cx = cy = size / 2
    radius = 120
    start_angle = -pi / 2
    n = len(values)

    def polar(r: float, i: int) -> Tuple[float, float]:
        a = start_angle + (2 * pi * i / n)
        return (cx + r * cos(a), cy + r * sin(a))

    def polar_angle(i: int) -> float:
        return start_angle + (2 * pi * i / n)

    axis_points: List[Tuple[float, float]] = [polar(radius, i) for i in range(n)]
    polygon_points: List[Tuple[float, float]] = []
    for i, v in enumerate(values):
        r = radius * (float(v["points"]) / max_points)
        polygon_points.append(polar(r, i))

    def fmt_points(points: List[Tuple[float, float]]) -> str:
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)

    rings: List[str] = []
    for k in range(1, 6):
        r = radius * (k / 5)
        ring_pts = [polar(r, i) for i in range(n)]
        rings.append(fmt_points(ring_pts))

    axis_lines: List[Dict[str, float]] = []
    for x, y in axis_points:
        axis_lines.append({"x2": float(x), "y2": float(y)})

    labels: List[Dict[str, object]] = []
    label_radius = radius + 26
    for i, v in enumerate(values):
        x, y = polar(label_radius, i)
        anchor = "middle"
        if x < cx - 10:
            anchor = "end"
        elif x > cx + 10:
            anchor = "start"
        labels.append(
            {
                "x": float(x),
                "y": float(y),
                "text": v["label"],
                "anchor": anchor,
            }
        )

    value_labels: List[Dict[str, object]] = []
    for i, v in enumerate(values):
        a = polar_angle(i)
        x, y = polygon_points[i]
        offset = 12
        lx = x + offset * cos(a)
        ly = y + offset * sin(a)
        anchor = "middle"
        if lx < cx - 10:
            anchor = "end"
        elif lx > cx + 10:
            anchor = "start"
        value_labels.append(
            {
                "x": float(lx),
                "y": float(ly),
                "text": str(v["points"]),
                "anchor": anchor,
            }
        )

    return {
        "size": size,
        "cx": cx,
        "cy": cy,
        "radius": radius,
        "max_points": max_points,
        "values": values,
        "rings": rings,
        "axis_lines": axis_lines,
        "polygon_points": fmt_points(polygon_points),
        "outer_points": fmt_points(axis_points),
        "labels": labels,
        "value_labels": value_labels,
    }


_load_dotenv()
app = create_app()

if __name__ == "__main__":
    app.run(debug=bool(app.config.get("DEBUG", False)))
