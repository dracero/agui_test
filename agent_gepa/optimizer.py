import dspy
from dspy.teleprompt import BootstrapFewShot, GEPA
from dspy_modules import RAGModule, Responder
import os
from dotenv import load_dotenv

load_dotenv()

# Configure DSPy with Gemini
gemini_key = os.getenv("GOOGLE_API_KEY")
lm = dspy.LM(model="gemini/gemini-2.5-flash", api_key=gemini_key)
dspy.settings.configure(lm=lm)

# --- Metric ---
class ResponseJudge(dspy.Signature):
    """Evaluates the quality of a physics explanation."""
    question = dspy.InputField()
    answer = dspy.InputField()
    score = dspy.OutputField(desc="A score between 0 and 10.")
    reasoning = dspy.OutputField()

def validate_response(gold, pred, trace=None, pred_name=None, pred_trace=None):
    # This is a simple LLM-based metric
    judge = dspy.ChainOfThought(ResponseJudge)
    result = judge(question=gold.user_query, answer=pred.response)
    try:
        score = float(result.score)
        return score / 10.0
    except:
        return 0.0

# --- Optimization Script ---
def optimize_agent():
    print("Starting optimization...")
    
    # 1. Define the module to optimize
    # We focus on optimizing the Responder for now as it's the most critical for quality
    student = dspy.ChainOfThought(Responder)
    
    # 2. Create a small dataset (Synthetic or Manual)
    # In a real scenario, this should be loaded from a file
    trainset = [
        dspy.Example(
            user_query="Un bloque de masa m baja por un plano inclinado con rozamiento. ¿Cuáles son las fuerzas que actúan y cómo planteo la segunda ley de Newton?",
            memory_context="No context",
            classification="Mecánica - Dinámica",
            retrieved_context="Diagrama de cuerpo libre: Peso (P), Normal (N), Fuerza de rozamiento (fr). Ecuaciones: ΣFx = m*ax, ΣFy = m*ay.",
            response="Las fuerzas que actúan sobre el bloque son: 1) El Peso (P), vertical hacia abajo. 2) La Normal (N), perpendicular al plano. 3) La fuerza de rozamiento (fr), opuesta al movimiento (hacia arriba del plano). Para plantear la 2da Ley de Newton, descomponemos el peso en ejes x (paralelo al plano) e y (perpendicular). Eje x: P*sen(θ) - fr = m*a. Eje y: N - P*cos(θ) = 0."
        ).with_inputs("user_query", "memory_context", "classification", "retrieved_context"),
        dspy.Example(
            user_query="¿Cuál es la diferencia entre una onda transversal y una longitudinal? Dame ejemplos.",
            memory_context="Vimos oscilaciones armónicas.",
            classification="Ondas",
            retrieved_context="Onda transversal: perturbación perpendicular a propagación. Onda longitudinal: perturbación paralela a propagación.",
            response="La diferencia principal radica en la dirección de oscilación del medio respecto a la propagación de la onda. En las ondas transversales, las partículas oscilan perpendicularmente a la dirección de avance (ej: luz, ondas en una cuerda). En las ondas longitudinales, oscilan en la misma dirección (ej: sonido, ondas en un resorte comprimido)."
        ).with_inputs("user_query", "memory_context", "classification", "retrieved_context"),
        dspy.Example(
            user_query="Explica la ley de Snell y qué sucede cuando la luz pasa de un medio con mayor índice de refracción a uno menor.",
            memory_context="No context",
            classification="Óptica Geométrica",
            retrieved_context="Ley de Snell: n1*sen(θ1) = n2*sen(θ2). Reflexión total interna ocurre si n1 > n2 y θ1 > θc.",
            response="La Ley de Snell relaciona los índices de refracción y los ángulos de incidencia y refracción: n1*sen(θ1) = n2*sen(θ2). Cuando la luz pasa de un medio de mayor índice (n1) a uno menor (n2), el rayo se aleja de la normal. Si el ángulo de incidencia supera el 'ángulo crítico', ocurre la reflexión total interna y no hay refracción."
        ).with_inputs("user_query", "memory_context", "classification", "retrieved_context"),
        dspy.Example(
            user_query="¿Cómo se calcula el centro de masa de un sistema de partículas discretas y qué representa físicamente?",
            memory_context="No context",
            classification="Sistemas de Partículas",
            retrieved_context="R_cm = (Σ mi * ri) / Σ mi. Representa el punto donde se concentra la masa para el análisis traslacional.",
            response="El centro de masa (CM) de un sistema de partículas discretas se calcula como el promedio ponderado de las posiciones por sus masas: R_cm = (Σ mi * ri) / M_total. Físicamente, representa el punto geométrico que se mueve como si toda la masa del sistema estuviera concentrada allí y todas las fuerzas externas actuaran sobre él."
        ).with_inputs("user_query", "memory_context", "classification", "retrieved_context"),
        dspy.Example(
            user_query="Define el momento de inercia y explica su rol en la energía cinética de rotación.",
            memory_context="Vimos rotación de cuerpo rígido.",
            classification="Cuerpo Rígido",
            retrieved_context="I = ∫ r^2 dm. K_rot = 1/2 * I * ω^2. Es el análogo a la masa en rotación.",
            response="El momento de inercia (I) es una medida de la resistencia de un cuerpo a cambiar su estado de rotación. Se define como I = Σ mi * ri^2 (o la integral para cuerpos continuos). En la energía cinética de rotación (K = 1/2 * I * ω^2), juega el mismo rol que la masa en la energía cinética traslacional: a mayor momento de inercia, más energía se requiere para alcanzar una misma velocidad angular."
        ).with_inputs("user_query", "memory_context", "classification", "retrieved_context"),
    ]
    
    # 3. Set up the optimizer
    # Using GEPA as requested
    # Create a reflection LM (using the same model but with higher temperature for creativity)
    reflection_lm = dspy.LM(model="gemini/gemini-2.5-flash", api_key=gemini_key, temperature=0.7)
    teleprompter = GEPA(metric=validate_response, max_metric_calls=50, reflection_lm=reflection_lm)
    
    # 4. Compile
    print("Compiling/Optimizing with GEPA...")
    # GEPA might have different arguments, but compile is standard
    optimized_responder = teleprompter.compile(student, trainset=trainset)
    
    # 5. Save
    optimized_responder.save("optimized_responder.json")
    print("Optimization complete. Saved to optimized_responder.json")

if __name__ == "__main__":
    optimize_agent()
