"""European Portuguese texts (pt-PT). Keys are the English texts used in the code (see i18n.py).

Placeholders in {braces} must be kept exactly as in the English text.
tests/test_i18n.py checks that every text used in the code has a translation here.
"""

# Column (variable) names shown to the user in Portuguese mode. They are also accepted as column
# headers when a file is read, in both languages ("__id__" = patient identifier, "__label__" = LP result).
COLUMN_NAMES = {
    "__id__": "id_doente",
    "__label__": "resultado_PL",
    "age": "idade",
    "sex": "sexo",
    "egfr": "TFGe",
    "creatinine": "creatinina",
    "triglycerides": "triglicéridos",
    "hemoglobin": "hemoglobina",
    "anemia": "anemia",
    "ptau217": "ptau217",
    "ab42": "ab42",
    "ab40": "ab40",
    "ab42_ab40_ratio": "rácio_ab42_ab40",
    "ptau217_ab42_ratio": "rácio_ptau217_ab42",
    "apoe4": "apoe4",
    "hypertension": "hipertensão",
    "stroke": "AVC",
    "clinical_stage": "estádio_clínico",
    "atypical_features": "sinais_atípicos",
    "bmi": "IMC",
    "sleep_apnea": "apneia_sono",
    "tsh": "TSH",
    "thyroid_disease": "doença_tiroideia",
    "mta_score": "MTA",
    "fazekas": "Fazekas",
    "mmse": "MMSE",
}

COLUMN_DESCRIPTIONS = {
    "bmi": "Índice de massa corporal (peso / altura^2) - IMC baixo aumenta a p-tau217 plasmática",
    "sleep_apnea": "Apneia obstrutiva do sono conhecida (diagnóstico ou CPAP), sim/não - associada a p-tau217 mais baixa",
    "tsh": "Hormona estimulante da tiroide (rastreio analítico de rotina na demência)",
    "thyroid_disease": "Doença da tiroide conhecida (hipo ou hipertiroidismo, ou sob levotiroxina / antitiroideus), sim/não",
    "mta_score": "Atrofia temporal mesial na RM (escala MTA de Scheltens, média esquerda/direita, 0-4) - em branco se não houver",
    "fazekas": "Hiperintensidades da substância branca na RM (Fazekas 0-3) - em branco se não houver",
    "mmse": "Mini-Mental State Examination (0-30) na consulta da colheita",
    "age": "Idade na colheita do plasma",
    "sex": "Sexo biológico (M = masculino, F = feminino)",
    "egfr": "Taxa de filtração glomerular estimada (em branco -> calculada a partir da creatinina com CKD-EPI 2021)",
    "creatinine": "Creatinina sérica (usada apenas para calcular a TFGe quando esta está em branco)",
    "triglycerides": "Triglicéridos séricos",
    "hemoglobin": "Hemoglobina (hemograma) - a anemia aumenta a p-tau217 plasmática",
    "anemia": "Anemia, definição da OMS (calculada a partir da hemoglobina e do sexo)",
    "ptau217": "p-tau217 plasmática (OBRIGATÓRIA; define a zona cinzenta)",
    "ab42": "Beta-amiloide 42 plasmática",
    "ab40": "Beta-amiloide 40 plasmática",
    "ab42_ab40_ratio": "Rácio Abeta42/Abeta40 plasmático (em branco -> calculado a partir de ab42 e ab40)",
    "ptau217_ab42_ratio": "p-tau217 / Abeta42 (calculado automaticamente)",
    "apoe4": "Número de alelos APOE e4 (0, 1, 2) ou genótipo em texto, por exemplo E3/E4",
    "hypertension": "Hipertensão conhecida (diagnóstico ou medicação anti-hipertensora), sim/não",
    "stroke": "Antecedentes de AVC ou AIT, sim/não",
    "clinical_stage": "Estádio clínico - DCS (declínio cognitivo subjetivo), DCL ou Demência",
    "atypical_features": ("SINAL DE ALARME - progressão rápida, doença do neurónio motor, suspeita de doença priónica, "
                          "parkinsonismo marcado, síndrome frontotemporal ou possível HPN (sim -> não classificado, "
                          "referenciar)"),
}

UNITS = {
    "years": "anos",
    "alleles": "alelos",
    "ratio": "rácio",
    "SCD/MCI/Dementia": "DCS/DCL/Demência",
    "text": "texto",
    "points": "pontos",
}

PT = {
    # --- decisions and short words ---------------------------------------------------------------
    "POSITIVE": "POSITIVO",
    "NEGATIVE": "NEGATIVO",
    "INCONCLUSIVE": "INCONCLUSIVO",
    "INCONCLUSIVE - refer to LP": "INCONCLUSIVO - referenciar para PL",
    "NOT APPLICABLE - outside grey zone": "NÃO APLICÁVEL - fora da zona cinzenta",
    "CHECK DATA": "VERIFICAR DADOS",
    "POSITIVE (rule-in)": "POSITIVO (confirmação)",
    "NEGATIVE (rule-out)": "NEGATIVO (exclusão)",
    "Positive": "Positivo",
    "Negative": "Negativo",
    "Positive/Negative": "Positivo/Negativo",
    "Positive or Negative": "Positivo ou Negativo",
    "SCD": "DCS",
    "MCI": "DCL",
    "Dementia": "Demência",
    "SCD, MCI or Dementia": "DCS, DCL ou Demência",
    "PPV": "VPP",
    "NPV": "VPN",
    "yes": "sim",
    "no": "não",
    "none": "nenhum",
    "n/a": "n/d",
    "n/a (no calls)": "n/d (sem classificações)",
    "Patient": "Doente",
    "Patients": "Doentes",
    "Decision": "Decisão",
    "Why": "Porquê",
    "Missing variables": "Variáveis em falta",
    "Notes": "Notas",
    "Model": "Modelo",
    "Figures": "Figuras",
    "Done": "Concluído",
    "Starting ...": "A iniciar ...",
    "Item": "Item",
    "Value": "Valor",
    "DISCLAIMER": "AVISO",
    "Invalid value": "Valor inválido",
    "Results": "Resultados",
    "Summary": "Resumo",
    "Input": "Dados de entrada",
    "Dictionary": "Dicionário",
    "Instructions": "Instruções",
    # result table headers
    "patient_id": "id_doente",
    "decision": "decisão",
    "explanation": "explicação",
    "missing_variables": "variáveis_em_falta",
    "notes": "notas",
    # template dictionary headers
    "column": "coluna",
    "description": "descrição",
    "unit": "unidade",
    "required": "obrigatório",
    "limits": "limites",
    "example": "exemplo",
    # file names
    "_with_predictions": "_com_previsoes",
    "_results": "_resultados",
    "patient_data_template.xlsx": "modelo_dados_doentes.xlsx",

    # --- prediction explanations -----------------------------------------------------------------
    "Research prototype for teaching purposes - not a medical device. Results must not be used for clinical "
    "decisions without validation in an independent cohort and regulatory/ethical approval.":
        "Protótipo de investigação para fins de ensino - não é um dispositivo médico. Os resultados não devem ser "
        "usados em decisões clínicas sem validação numa coorte independente e sem aprovação ética/regulamentar.",
    "cross-validated {kind} {pv:.1%} (one-sided {conf:.0%} lower bound {lb:.1%}; {k}/{n} training calls correct)":
        "{kind} em validação cruzada {pv:.1%} (limite inferior unilateral a {conf:.0%}: {lb:.1%}; {k}/{n} "
        "classificações corretas no treino)",
    "Data problem: {issues}. Correct the value(s) and run again.":
        "Problema nos dados: {issues}. Corrija o(s) valor(es) e corra de novo.",
    "p-tau217 = {v:g} pg/mL is outside the grey zone [{lo}-{hi}]: Stage-1 result is {stage1}. The model was "
    "trained only on grey-zone patients and was not applied.":
        "p-tau217 = {v:g} pg/mL está fora da zona cinzenta [{lo}-{hi}]: o resultado da etapa 1 é {stage1}. O "
        "modelo foi treinado apenas com doentes da zona cinzenta e não foi aplicado.",
    "Red flag present ({flags}): atypical presentation, plasma p-tau217 is not reliable here. The model was not "
    "applied. Refer to lumbar puncture / PET.":
        "Sinal de alarme presente ({flags}): apresentação atípica, a p-tau217 plasmática não é fiável neste caso. "
        "O modelo não foi aplicado. Referenciar para punção lombar / PET.",
    "Insufficient data: {miss:.0%} of the model variables are missing (limit {limit:.0%}). Refer to lumbar "
    "puncture.":
        "Dados insuficientes: faltam {miss:.0%} das variáveis do modelo (limite {limit:.0%}). Referenciar para "
        "punção lombar.",
    "rule-out <= {t:.2f}": "exclusão <= {t:.2f}",
    "rule-in >= {t:.2f}": "confirmação >= {t:.2f}",
    "no safe rule-out threshold": "sem limiar de exclusão seguro",
    "no safe rule-in threshold": "sem limiar de confirmação seguro",
    "{f} = {v:g} outside the range seen in training [{lo:g}-{hi:g}]":
        "{f} = {v:g} fora do intervalo observado no treino [{lo:g}-{hi:g}]",

    # --- Excel outputs ---------------------------------------------------------------------------
    "AI decision": "IA decisão",
    "AI explanation": "IA explicação",
    "AI missing variables": "IA variáveis em falta",
    "AI notes": "IA notas",
    "AI prediction info": "Informação da previsão IA",
    "Generated": "Gerado em",
    "Model trained": "Modelo treinado em",
    "Training data": "Dados de treino",
    "Training patients (grey zone)": "Doentes de treino (zona cinzenta)",
    "Grey zone (p-tau217, pg/mL)": "Zona cinzenta (p-tau217, pg/mL)",
    "none (not certified)": "nenhum (não certificado)",
    "Target PPV / NPV": "VPP / VPN alvo",
    "Confidence bound required": "Limite de confiança exigido",
    "Safety target": "Alvo de segurança",
    "PPV >= {ppv:.0%}, NPV >= {npv:.0%}": "VPP >= {ppv:.0%}, VPN >= {npv:.0%}",
    " (one-sided {conf:.0%} lower bound)": " (limite inferior unilateral a {conf:.0%})",
    " (point estimate)": " (estimativa pontual)",
    "Patients: {decision}": "Doentes: {decision}",

    # --- reading files ---------------------------------------------------------------------------
    "Cannot determine the file type (missing file name).":
        "Não foi possível determinar o tipo de ficheiro (falta o nome do ficheiro).",
    "Old .xls format is not supported: open it in Excel and 'Save as' .xlsx.":
        "O formato antigo .xls não é suportado: abra-o no Excel e use 'Guardar como' .xlsx.",
    "Unsupported file type '{suffix}'. Use .xlsx or .csv.": "Tipo de ficheiro '{suffix}' não suportado. Use .xlsx ou .csv.",
    "invalid number '{value}'": "número inválido '{value}'",
    "censored value '{text}' used as {value}": "valor censurado '{text}' usado como {value}",
    "invalid sex '{value}' (use M or F)": "sexo inválido '{value}' (use M ou F)",
    "invalid yes/no value '{value}'": "valor sim/não inválido '{value}'",
    "invalid APOE e4 allele count '{value}' (0, 1 or 2)": "número de alelos APOE e4 inválido '{value}' (0, 1 ou 2)",
    "APOE e4 'carrier' coded as 1 allele": "APOE e4 'portador' codificado como 1 alelo",
    "invalid APOE value '{value}' (use 0/1/2 or e.g. E3/E4)": "valor de APOE inválido '{value}' (use 0/1/2 ou, p. ex., E3/E4)",
    "invalid clinical stage '{value}' (SCD, MCI or Dementia)": "estádio clínico inválido '{value}' (DCS, DCL ou Demência)",
    "Column '{header}' ignored: '{other}' already provides '{target}'.":
        "Coluna '{header}' ignorada: '{other}' já fornece '{target}'.",
    "{name} = {value:g} below plausible minimum {limit:g} {unit}": "{name} = {value:g} abaixo do mínimo plausível {limit:g} {unit}",
    "{name} = {value:g} above plausible maximum {limit:g} {unit}": "{name} = {value:g} acima do máximo plausível {limit:g} {unit}",
    "The file contains no patient rows.": "O ficheiro não contém linhas de doentes.",
    "Required column 'ptau217' (plasma p-tau217, pg/mL) was not found.":
        "A coluna obrigatória 'ptau217' (p-tau217 plasmática, pg/mL) não foi encontrada.",
    "Training needs the lumbar-puncture result column '{label}' (Positive / Negative).":
        "O treino precisa da coluna com o resultado da punção lombar '{label}' (Positivo / Negativo).",
    "Excel row {row}: missing patient_id, using 'row_{row}'.": "Linha {row} do Excel: falta o id_doente, usado 'row_{row}'.",
    "No 'patient_id' column found: rows are identified by their Excel row number.":
        "Não foi encontrada a coluna 'id_doente': as linhas são identificadas pelo número da linha no Excel.",
    "Duplicated patient_id values: {ids}.": "Valores de id_doente repetidos: {ids}.",
    "eGFR computed from creatinine (CKD-EPI 2021)": "TFGe calculada a partir da creatinina (CKD-EPI 2021)",
    " (computed)": " (calculado)",
    "ptau217 missing (required)": "ptau217 em falta (obrigatória)",
    "Variables not present in this file (treated as missing): {names}.":
        "Variáveis ausentes neste ficheiro (tratadas como em falta): {names}.",
    "Columns not used (not defined in config.yaml): {names}. To use a new variable, add it to the 'features' list "
    "in config.yaml and retrain.":
        "Colunas não usadas (não definidas em config.yaml): {names}. Para usar uma nova variável, acrescente-a à "
        "lista 'features' em config.yaml e volte a treinar.",
    "Patient {pid}: lumbar-puncture result '{value}' not understood (use Positive/Negative).":
        "Doente {pid}: resultado da punção lombar '{value}' não reconhecido (use Positivo/Negativo).",
    "No usable lumbar-puncture results (Positive/Negative) were found.":
        "Não foram encontrados resultados de punção lombar utilizáveis (Positivo/Negativo).",

    # --- training --------------------------------------------------------------------------------
    "The training file has no lumbar-puncture result column.":
        "O ficheiro de treino não tem a coluna com o resultado da punção lombar.",
    "{n} patient(s) with p-tau217 outside the grey zone were excluded from training.":
        "{n} doente(s) com p-tau217 fora da zona cinzenta foram excluídos do treino.",
    "{n} row(s) without a usable LP result were excluded.": "{n} linha(s) sem resultado de PL utilizável foram excluídas.",
    "{n} row(s) without p-tau217 were excluded.": "{n} linha(s) sem p-tau217 foram excluídas.",
    "Too few patients: {pos} LP-positive and {neg} LP-negative in the grey zone (at least {k} of each are "
    "required; several hundred are recommended).":
        "Doentes insuficientes: {pos} com PL positiva e {neg} com PL negativa na zona cinzenta (são precisos pelo "
        "menos {k} de cada; recomendam-se várias centenas).",
    "Variables with no data in the training file (not used by the model): {names}.":
        "Variáveis sem dados no ficheiro de treino (não usadas pelo modelo): {names}.",
    "Variables missing in more than 40% of patients: {names}.": "Variáveis em falta em mais de 40% dos doentes: {names}.",
    "{n} training patient(s) had implausible/invalid values; those values were treated as missing (see the OOF "
    "predictions file).":
        "{n} doente(s) de treino tinham valores implausíveis/inválidos; esses valores foram tratados como em falta "
        "(ver o ficheiro de previsões fora da partição).",
    "No threshold reached the safety target for {word} calls with the current data: the model will never call a "
    "patient {side}. More patients are needed.":
        "Nenhum limiar atingiu o alvo de segurança para as classificações {word} com os dados atuais: o modelo "
        "nunca classificará um doente como {side}. São precisos mais doentes.",
    "{path} is not a model file produced by this project (or an old version).":
        "{path} não é um ficheiro de modelo produzido por este projeto (ou é de uma versão antiga).",
    "Cross-validation: fit {k}/{n}": "Validação cruzada: ajuste {k}/{n}",
    "Nested validation: outer fold {k}/{n}": "Validação aninhada: partição externa {k}/{n}",

    # --- report and figures ----------------------------------------------------------------------
    "{v:.1%} (95% CI {lo:.1%}-{hi:.1%}; {k}/{n})": "{v:.1%} (IC 95% {lo:.1%}-{hi:.1%}; {k}/{n})",
    "LP negative": "PL negativa",
    "LP positive": "PL positiva",
    "{name}\n(patients)": "{name}\n(doentes)",
    "NEGATIVE\nscore <= {t:.2f}": "NEGATIVO\npontuação <= {t:.2f}",
    "INCONCLUSIVE\n-> lumbar puncture": "INCONCLUSIVO\n-> punção lombar",
    "POSITIVE\nscore >= {t:.2f}": "POSITIVO\npontuação >= {t:.2f}",
    "p-tau217 alone  AUC {v:.2f}": "p-tau217 isolada  AUC {v:.2f}",
    "1 - specificity": "1 - especificidade",
    "Sensitivity": "Sensibilidade",
    "Discrimination inside the grey zone\n(cross-validated)": "Discriminação dentro da zona cinzenta\n(validação cruzada)",
    "{metric} (estimate)": "{metric} (estimativa)",
    "{metric} one-sided {conf:.0%} lower bound": "{metric} limite inferior unilateral a {conf:.0%}",
    "target {t:.0%}": "alvo {t:.0%}",
    "Rule-out (NEGATIVE if score <= t)": "Exclusão (NEGATIVO se pontuação <= t)",
    "Rule-in (POSITIVE if score >= t)": "Confirmação (POSITIVO se pontuação >= t)",
    "patients called": "doentes classificados",
    " chosen t = {t:.2f}": " t escolhido = {t:.2f}",
    "Decrease in cross-validated AUC when the variable is shuffled":
        "Diminuição da AUC em validação cruzada quando a variável é baralhada",
    "Permutation importance": "Importância por permutação",
    "one-sided {conf:.0%} Clopper-Pearson lower bound >= target":
        "limite inferior unilateral de Clopper-Pearson a {conf:.0%} >= alvo",
    "point estimate >= target (exploratory mode)": "estimativa pontual >= alvo (modo exploratório)",
    "*Trained {created}* - source: `{source}`": "*Treinado em {created}* - origem: `{source}`",
    "## Cohort": "## Coorte",
    "- Rows in file: {rows}; excluded: {no_lp} without LP result, {no_ptau} without p-tau217, {outside} outside "
    "the grey zone [{lo}-{hi} pg/mL].":
        "- Linhas no ficheiro: {rows}; excluídas: {no_lp} sem resultado de PL, {no_ptau} sem p-tau217, {outside} "
        "fora da zona cinzenta [{lo}-{hi} pg/mL].",
    "- **Training patients: {n}** ({pos} LP-positive, {neg} LP-negative; prevalence {prev:.1%}).":
        "- **Doentes de treino: {n}** ({pos} com PL positiva, {neg} com PL negativa; prevalência {prev:.1%}).",
    "- Variables used ({k}): {names}.": "- Variáveis usadas ({k}): {names}.",
    "## Discrimination (repeated cross-validation)": "## Discriminação (validação cruzada repetida)",
    "- p-tau217 alone (inside the grey zone): AUC {auc:.3f} (95% CI {lo:.3f}-{hi:.3f}).":
        "- p-tau217 isolada (dentro da zona cinzenta): AUC {auc:.3f} (IC 95% {lo:.3f}-{hi:.3f}).",
    "## Decision thresholds used for new patients": "## Limiares de decisão usados para novos doentes",
    "Rule: PPV >= {ppv:.0%} for POSITIVE calls and NPV >= {npv:.0%} for NEGATIVE calls, using the {rule}.":
        "Regra: VPP >= {ppv:.0%} para as classificações POSITIVO e VPN >= {npv:.0%} para as classificações "
        "NEGATIVO, usando o critério {rule}.",
    "none could be certified": "nenhum pôde ser certificado",
    "Everything between the two thresholds is **INCONCLUSIVE -> lumbar puncture**.":
        "Tudo o que fica entre os dois limiares é **INCONCLUSIVO -> punção lombar**.",
    "## Honest estimate for NEW patients (nested cross-validation)":
        "## Estimativa honesta para NOVOS doentes (validação cruzada aninhada)",
    "The whole procedure (cross-validation, threshold selection, final model) was repeated in {k} outer folds and "
    "applied to patients it had never seen:":
        "Todo o procedimento (validação cruzada, escolha dos limiares, modelo final) foi repetido em {k} partições "
        "externas e aplicado a doentes que nunca tinha visto:",
    "- **Lumbar punctures avoided (patients resolved): {v}**": "- **Punções lombares evitadas (doentes decididos): {v}**",
    "- PPV of POSITIVE calls: {v}": "- VPP das classificações POSITIVO: {v}",
    "- NPV of NEGATIVE calls: {v}": "- VPN das classificações NEGATIVO: {v}",
    "- Wrong calls: {e} ({fp} false positive, {fn} false negative) out of {n} grey-zone patients":
        "- Classificações erradas: {e} ({fp} falso(s) positivo(s), {fn} falso(s) negativo(s)) em {n} doentes da "
        "zona cinzenta",
    "- Remaining INCONCLUSIVE (sent to LP): {v}": "- INCONCLUSIVOS restantes (enviados para PL): {v}",
    "- Thresholds chosen in each outer fold: {v}": "- Limiares escolhidos em cada partição externa: {v}",
    "pos {p} / neg {n}": "pos {p} / neg {n}",
    "## Honest estimate for new patients": "## Estimativa honesta para novos doentes",
    "Nested cross-validation was switched off: the numbers above are optimistic because the thresholds were chosen "
    "on the same data. Re-train with nested validation for an honest estimate.":
        "A validação cruzada aninhada estava desligada: os números acima são otimistas porque os limiares foram "
        "escolhidos nos mesmos dados. Volte a treinar com validação aninhada para uma estimativa honesta.",
    "## How many patients does the {conf:.0%} rule need?": "## Quantos doentes exige a regra dos {conf:.0%}?",
    "To prove PPV/NPV >= {t:.0%} with {conf:.0%} confidence, a threshold must classify at least: {v}.":
        "Para demonstrar VPP/VPN >= {t:.0%} com {conf:.0%} de confiança, um limiar tem de classificar pelo menos: "
        "{v}.",
    "{v} patients with {k} error(s)": "{v} doentes com {k} erro(s)",
    "## Most informative variables (permutation importance)": "## Variáveis mais informativas (importância por permutação)",
    "{i}. {name} (AUC drop {v:.3f})": "{i}. {name} (queda da AUC {v:.3f})",
    "## Warnings": "## Avisos",
    "Research prototype - not a medical device. Validate on an independent cohort before any clinical use.":
        "Protótipo de investigação - não é um dispositivo médico. Validar numa coorte independente antes de "
        "qualquer uso clínico.",

    # --- Excel template --------------------------------------------------------------------------
    "Unique patient identifier (pseudonymised!)": "Identificador único do doente (pseudonimizado!)",
    "no (blank = missing)": "não (em branco = em falta)",
    "Lumbar-puncture (CSF) result. Fill for the TRAINING file; leave blank or delete the column for new patients.":
        "Resultado da punção lombar (LCR). Preencher no ficheiro de TREINO; deixar em branco ou apagar a coluna "
        "para novos doentes.",
    "training only": "apenas no treino",
    "Use M (male) or F (female)": "Use M (masculino) ou F (feminino)",
    "HOW TO FILL THIS FILE": "COMO PREENCHER ESTE FICHEIRO",
    "1. One row per patient in the sheet 'Patients'. Do not rename that sheet. Delete the example row.":
        "1. Uma linha por doente na folha 'Doentes'. Não mude o nome dessa folha. Apague a linha de exemplo.",
    "2. Keep the column names. Units in brackets are optional. Extra columns are ignored.":
        "2. Mantenha os nomes das colunas. As unidades entre parênteses são opcionais. Colunas extra são ignoradas.",
    "3. Leave a cell blank when a value is not available (the model handles missing values).":
        "3. Deixe a célula em branco quando um valor não estiver disponível (o modelo lida com valores em falta).",
    "4. Use the units shown. Decimal comma (0,25) or point (0.25) are both accepted.":
        "4. Use as unidades indicadas. São aceites vírgula decimal (0,25) e ponto decimal (0.25).",
    "5. The model is only applied to patients with plasma p-tau217 between {lo} and {hi} pg/mL (grey zone).":
        "5. O modelo só é aplicado a doentes com p-tau217 plasmática entre {lo} e {hi} pg/mL (zona cinzenta).",
    "6. Training file: fill '{label}' (Positive/Negative) for every patient.":
        "6. Ficheiro de treino: preencha '{label}' (Positivo/Negativo) para todos os doentes.",
    "   New patients: leave '{label}' blank or delete the column.":
        "   Novos doentes: deixe '{label}' em branco ou apague a coluna.",
    "7. Use pseudonymised identifiers only - never names or hospital record numbers.":
        "7. Use apenas identificadores pseudonimizados - nunca nomes nem números de processo hospitalar.",
    "8. eGFR may be left blank if serum creatinine is given (computed with CKD-EPI 2021).":
        "8. A TFGe pode ficar em branco se a creatinina sérica for indicada (calculada com CKD-EPI 2021).",

    # --- app -------------------------------------------------------------------------------------
    "Grey-zone AD triage": "Triagem DA na zona cinzenta",
    "Runs locally: files are processed in memory on this computer and are not sent anywhere.":
        "Funciona localmente: os ficheiros são processados em memória neste computador e não são enviados para "
        "lado nenhum.",
    "Loading model ...": "A carregar o modelo ...",
    "not found": "não foi encontrado",
    "not compatible with this installation": "não é compatível com esta instalação",
    "Could not train the default model: {exc}": "Não foi possível treinar o modelo padrão: {exc}",
    "Could not load this model: {exc}": "Não foi possível carregar este modelo: {exc}",
    "**Trained:** {created}  \n**Training patients:** {n}  \n**Grey zone:** {lo}-{hi} pg/mL  \n**POSITIVE if score "
    ">=** {pos}  \n**NEGATIVE if score <=** {neg}":
        "**Treinado em:** {created}  \n**Doentes de treino:** {n}  \n**Zona cinzenta:** {lo}-{hi} pg/mL  \n"
        "**POSITIVO se pontuação >=** {pos}  \n**NEGATIVO se pontuação <=** {neg}",
    "**Expected LPs avoided:** {v:.0%} (nested CV, {e} wrong calls / {n})":
        "**PL evitadas esperadas:** {v:.0%} (validação aninhada, {e} classificações erradas / {n})",
    "**Default model** trained on `{file}`  \nSHA-256 `{sha}...`":
        "**Modelo padrão** treinado com `{file}`  \nSHA-256 `{sha}...`",
    "The default dataset file has changed since this model was trained. Re-train it: python train.py --default":
        "O ficheiro de dados padrão mudou desde que este modelo foi treinado. Volte a treiná-lo: "
        "RETREINAR_MODELO_PADRAO.bat (ou python train.py --default)",
    "This model was trained on SYNTHETIC data (demo only).":
        "Este modelo foi treinado com dados SINTÉTICOS (apenas demonstração).",
    "No trained model yet - use the 'Train model' tab.":
        "Ainda não há nenhum modelo treinado - use o separador 'Treinar modelo'.",
    "Classify new patients": "Classificar novos doentes",
    "Train model": "Treinar modelo",
    "Model report": "Relatório do modelo",
    "Template & help": "Modelo de ficheiro e ajuda",
    "The file could not be used: {exc}": "Não foi possível usar o ficheiro: {exc}",
    "The file could not be read ({kind}: {exc}). Is it a valid .xlsx/.csv file?":
        "Não foi possível ler o ficheiro ({kind}: {exc}). É um ficheiro .xlsx/.csv válido?",
    "INCONCLUSIVE -> LP": "INCONCLUSIVO -> PL",
    "Outside grey zone": "Fora da zona cinzenta",
    "Check data": "Verificar dados",
    "**{r} of {n} grey-zone patients ({p:.0%}) received a definite answer; {i} remain inconclusive and should have "
    "a lumbar puncture.**":
        "**{r} de {n} doentes da zona cinzenta ({p:.0%}) receberam uma resposta definitiva; {i} continuam "
        "inconclusivos e devem fazer punção lombar.**",
    "{n} patient(s) have implausible or invalid values and were NOT classified. Correct the file and upload it "
    "again.":
        "{n} doente(s) têm valores implausíveis ou inválidos e NÃO foram classificados. Corrija o ficheiro e "
        "carregue-o de novo.",
    "File notes ({n})": "Notas sobre o ficheiro ({n})",
    "Show decisions": "Mostrar decisões",
    "Download my file with the predictions added": "Descarregar o meu ficheiro com as previsões acrescentadas",
    "Download results report (Excel)": "Descarregar o relatório de resultados (Excel)",
    "Separate workbook: results table, summary and a copy of the input.":
        "Livro separado: tabela de resultados, resumo e uma cópia dos dados de entrada.",
    "Classify new grey-zone patients": "Classificar novos doentes da zona cinzenta",
    "Drag and drop an Excel (.xlsx) or CSV file with one row per patient, in the layout of the template (see "
    "*Template & help*). Each patient is classified as **POSITIVE**, **NEGATIVE** or **INCONCLUSIVE - refer to "
    "LP**. A definite answer is only given when the model has demonstrated at least {ppv:.0%} PPV / {npv:.0%} NPV "
    "for patients with that score; everybody else stays inconclusive.":
        "Arraste e largue um ficheiro Excel (.xlsx) ou CSV com uma linha por doente, com a estrutura do modelo de "
        "ficheiro (ver *Modelo de ficheiro e ajuda*). Cada doente é classificado como **POSITIVO**, **NEGATIVO** ou "
        "**INCONCLUSIVO - referenciar para PL**. Só é dada uma resposta definitiva quando o modelo demonstrou pelo "
        "menos {ppv:.0%} de VPP / {npv:.0%} de VPN para doentes com essa pontuação; todos os outros ficam "
        "inconclusivos.",
    "No trained model available. Go to **Train model** first (the synthetic demo file can be used to try the "
    "tool).":
        "Não há nenhum modelo treinado. Vá primeiro a **Treinar modelo** (pode usar o ficheiro sintético de "
        "demonstração para experimentar a ferramenta).",
    "Drag and drop the patient file here": "Arraste e largue aqui o ficheiro dos doentes",
    "Train a new model": "Treinar um novo modelo",
    "Drag and drop the training file here": "Arraste e largue aqui o ficheiro de treino",
    "Honest validation with nested cross-validation (recommended, ~1 minute)":
        "Validação honesta com validação cruzada aninhada (recomendado, ~1 minuto)",
    "Model name": "Nome do modelo",
    "Use the new model now": "Usar já o novo modelo",
    "No model selected.": "Nenhum modelo selecionado.",
    "How the thresholds were chosen: predictive value and its lower confidence bound for every candidate "
    "threshold.":
        "Como foram escolhidos os limiares: valor preditivo e o seu limite inferior de confiança para cada limiar "
        "candidato.",
    "Download out-of-fold predictions of the training patients":
        "Descarregar as previsões fora da partição dos doentes de treino",
    "Input file layout": "Estrutura do ficheiro de entrada",
    "One row per patient in a sheet called **Patients**. Column names must match the list below (units in brackets "
    "are optional, upper/lower case does not matter). Blank cell = missing value. Only `ptau217` is mandatory.":
        "Uma linha por doente numa folha chamada **Doentes**. Os nomes das colunas têm de corresponder à lista "
        "abaixo (as unidades entre parênteses são opcionais, maiúsculas/minúsculas não importam; os nomes em inglês "
        "também são aceites). Célula em branco = valor em falta. Só `ptau217` é obrigatória.",
    "Download the Excel template": "Descarregar o modelo de ficheiro Excel",
    "Synthetic demo files": "Ficheiros sintéticos de demonstração",
    "Artificial patients, generated by `make_demo_data.py`, to try the tool. **Not real data.**":
        "Doentes artificiais, gerados por `make_demo_data.py`, para experimentar a ferramenta. **Não são dados "
        "reais.**",
    "Default training dataset (with LP)": "Conjunto de treino padrão (com PL)",
    "New patients (without LP)": "Novos doentes (sem PL)",
    "Answer key of the new patients": "Respostas corretas dos novos doentes",
    "How the decision is made": "Como é tomada a decisão",
    "It requires the **lower bound of the one-sided {conf:.0%} confidence interval** to reach the target, so the "
    "target is demonstrated statistically, not just observed.":
        "Exige que o **limite inferior do intervalo de confiança unilateral a {conf:.0%}** atinja o alvo, para que "
        "o alvo seja demonstrado estatisticamente e não apenas observado.",
    "Only the point estimate must reach the target (exploratory mode).":
        "Basta que a estimativa pontual atinja o alvo (modo exploratório).",

    # --- launcher and command line ---------------------------------------------------------------
    "No free port found between 8501 and 8550.": "Não foi encontrada nenhuma porta livre entre 8501 e 8550.",
    "Port {first} is busy (is the app already open in another window?). Using port {port}.":
        "A porta {first} está ocupada (a aplicação já está aberta noutra janela?). A usar a porta {port}.",
    "Starting the app... the first start can take up to a minute.":
        "A iniciar a aplicação... o primeiro arranque pode demorar até um minuto.",
    "Keep this window open while you use the app. Close it (or press Ctrl+C) to stop.":
        "Mantenha esta janela aberta enquanto usa a aplicação. Feche-a (ou carregue em Ctrl+C) para parar.",
    "ERROR: the app stopped while starting (see the messages above).":
        "ERRO: a aplicação parou durante o arranque (ver as mensagens acima).",
    "The app is taking unusually long. Try opening {url} in your browser yourself.":
        "A aplicação está a demorar mais do que o normal. Experimente abrir {url} no navegador.",
    "==> The app is ready: {url}  ({s:.0f} s)": "==> A aplicação está pronta: {url}  ({s:.0f} s)",
    "Open that address in your web browser.": "Abra esse endereço no navegador.",
    "Training the DEFAULT model from {file} ...": "A treinar o modelo PADRÃO a partir de {file} ...",
    "Default model saved to {folder} (with manifest.json).": "Modelo padrão guardado em {folder} (com manifest.json).",
    "ERROR: {exc}": "ERRO: {exc}",
    "Training on {file} ...": "A treinar com {file} ...",
    "Finished in {s:.0f} s. Model saved to {path}": "Concluído em {s:.0f} s. Modelo guardado em {path}",
    "ERROR: no model found at {path}. Train one first with train.py.":
        "ERRO: não foi encontrado nenhum modelo em {path}. Treine primeiro um modelo com train.py.",
    "Note: {message}": "Nota: {message}",
    "Results written to {out}": "Resultados gravados em {out}",
    "Original file with predictions added: {path}": "Ficheiro original com as previsões acrescentadas: {path}",

    # --- model choice and comparison --------------------------------------------------------------
    'Fitting the final model':
        'A ajustar o modelo final',
    'Cross-validated {model} scores':
        'Pontuações {model} em validação cruzada',
    '{model} score (out-of-fold)':
        'Pontuação {model} (fora da partição)',
    '# Training report - grey-zone {model}':
        '# Relatório de treino - {model} da zona cinzenta',
    '- Model: **{model}** ({params}).':
        '- Modelo: **{model}** ({params}).',
    '- {model} AUC: **{auc:.3f}** (95% CI {lo:.3f}-{hi:.3f}); {folds}-fold x {repeats} repeats, AUC per repeat {mn:.3f}-{mx:.3f}.':
        '- AUC do {model}: **{auc:.3f}** (IC 95% {lo:.3f}-{hi:.3f}); {folds} partições x {repeats} repetições, AUC por repetição {mn:.3f}-{mx:.3f}.',
    '| Call | Threshold on score | Training calls | Correct | Estimate | Lower bound |':
        '| Classificação | Limiar da pontuação | Classificações no treino | Corretas | Estimativa | Limite inferior |',
    '{model}  AUC {v:.2f}':
        '{model}  AUC {v:.2f}',
    'threshold t on the model score':
        'limiar t da pontuação do modelo',
    'Lumbar punctures avoided in nested validation (95% CI)':
        'Punções lombares evitadas na validação aninhada (IC 95%)',
    'Mean model score (out-of-fold)':
        'Pontuação média do modelo (fora da partição)',
    'Observed share LP-positive':
        'Proporção observada com PL positiva',
    'Calibration (closer to the diagonal = better)':
        'Calibração (mais perto da diagonal = melhor)',
    'All models agree':
        'Todos os modelos concordam',
    'AUC (95% CI)':
        'AUC (IC 95%)',
    'Brier score':
        'Score de Brier',
    'POSITIVE if score >=':
        'POSITIVO se pontuação >=',
    'NEGATIVE if score <=':
        'NEGATIVO se pontuação <=',
    'AUC difference (95% CI)':
        'Diferença de AUC (IC 95%)',
    'AUC difference significant?':
        'Diferença de AUC significativa?',
    'LPs avoided difference significant?':
        'Diferença de PL evitadas significativa?',
    '{v:.0%} ({e} wrong)':
        '{v:.0%} ({e} erradas)',
    'LPs avoided difference (95% CI)':
        'Diferença de PL evitadas (IC 95%)',
    'Wrong-call difference (95% CI)':
        'Diferença de classificações erradas (IC 95%)',
    'LPs avoided (nested)':
        'PL evitadas (aninhada)',
    'Wrong calls (FP / FN)':
        'Classificações erradas (FP / FN)',
    'PPV (nested)':
        'VPP (aninhada)',
    'NPV (nested)':
        'VPN (aninhada)',
    'score':
        'pontuação',
    'Score':
        'Pontuação',
    'AI model':
        'IA modelo',
    'AI score':
        'IA pontuação',
    'Model type':
        'Tipo de modelo',
    'Rule-in threshold (score >=)':
        'Limiar de confirmação (pontuação >=)',
    'Rule-out threshold (score <=)':
        'Limiar de exclusão (pontuação <=)',
    '{model} score {s:.3f} >= rule-in threshold {t:.2f}; {pv}.':
        'Pontuação {model} {s:.3f} >= limiar de confirmação {t:.2f}; {pv}.',
    '{model} score {s:.3f} <= rule-out threshold {t:.2f}; {pv}.':
        'Pontuação {model} {s:.3f} <= limiar de exclusão {t:.2f}; {pv}.',
    '{model} score {s:.3f} is not in a zone with demonstrated PPV/NPV >= {ppv:.0%}/{npv:.0%} ({parts}). Refer to lumbar puncture.':
        'A pontuação {model} {s:.3f} não está numa zona com VPP/VPN >= {ppv:.0%}/{npv:.0%} demonstrado ({parts}). Referenciar para punção lombar.',
    'ML model':
        'Modelo de ML',
    '{model} on plasma and clinical data of patients with p-tau217 in the grey zone.':
        '{model} com dados plasmáticos e clínicos de doentes com p-tau217 na zona cinzenta.',
    'Trained model':
        'Modelo treinado',
    "Algorithm that computes the score. Every model uses the same training procedure, the same {ppv:.0%} PPV / {npv:.0%} NPV rule with {conf:.0%} confidence and the same safety checks. See the tab 'Compare models'.":
        "Algoritmo que calcula a pontuação. Todos os modelos usam o mesmo procedimento de treino, a mesma regra de {ppv:.0%} de VPP / {npv:.0%} de VPN com {conf:.0%} de confiança e as mesmas verificações de segurança. Ver o separador 'Comparar modelos'.",
    'Compare models':
        'Comparar modelos',
    'Model in use: **{model}** (change it at the top right).':
        'Modelo em uso: **{model}** (mude-o no canto superior direito).',
    'Drag and drop the **training file**: grey-zone patients with their variables **and** the lumbar-puncture result in the column `lp_result` (Positive/Negative). Settings (grey-zone cut-offs, PPV/NPV targets, model parameters, list of variables) are read from `config.yaml`.':
        'Arraste e largue o **ficheiro de treino**: doentes da zona cinzenta com as suas variáveis **e** o resultado da punção lombar na coluna `resultado_PL` (ou `lp_result`) (Positivo/Negativo). As definições (pontos de corte da zona cinzenta, alvos de VPP/VPN, parâmetros dos modelos, lista de variáveis) são lidas de `config.yaml`.',
    'Train every model type on this file (needed for a fair comparison)':
        'Treinar todos os tipos de modelo com este ficheiro (necessário para uma comparação justa)',
    'Will train: {models}':
        'Vai treinar: {models}',
    'Comparing the models ...':
        'A comparar os modelos ...',
    'Compare the models':
        'Comparar os modelos',
    'All models are trained with the same procedure, on the same patients and the same random splits, and must meet the same rule (PPV >= {ppv:.0%} and NPV >= {npv:.0%}, proven with {conf:.0%} confidence) before they may call a patient POSITIVE or NEGATIVE. The best model is the one that **avoids the most lumbar punctures in nested validation without more wrong calls**; AUC only measures how well the scores are ordered.':
        'Todos os modelos são treinados com o mesmo procedimento, com os mesmos doentes e as mesmas partições aleatórias, e têm de cumprir a mesma regra (VPP >= {ppv:.0%} e VPN >= {npv:.0%}, demonstrados com {conf:.0%} de confiança) antes de poderem classificar um doente como POSITIVO ou NEGATIVO. O melhor modelo é o que **evita mais punções lombares na validação aninhada sem mais classificações erradas**; a AUC só mede se as pontuações estão bem ordenadas.',
    'Models to compare':
        'Modelos a comparar',
    '\n1. **Stage 1 (already done at the centre):** plasma p-tau217 < {lo} pg/mL is negative, > {hi} pg/mL is\n   positive. Only patients in between are analysed here.\n2. **Model ({model}, chosen at the top right):** combines all variables into a score between 0 and 1. Missing\n   values are handled inside the trees (Random Forest, Extra Trees, Gradient Boosting) or replaced by the training\n   median plus a "was missing" indicator (Logistic Regression, SVM).\n3. **Safety thresholds:** during training every patient receives a cross-validated score (from models that never\n   saw them). The tool then finds the lowest score above which at least {ppv:.0%} of patients were LP-positive\n   (PPV) and the highest score below which at least {npv:.0%} were LP-negative (NPV). {bound}\n4. **Everything in between stays INCONCLUSIVE** and is referred to lumbar puncture, exactly as before.\n5. **Safety checks:** patients outside the grey zone are not classified by the model; implausible values\n   (e.g. haemoglobin = 45 g/dL) block the classification; patients with a red flag (atypical features) or missing\n   more than {miss:.0%} of the variables stay inconclusive.\n':
        '\n1. **Etapa 1 (já feita no centro):** p-tau217 plasmática < {lo} pg/mL é negativa, > {hi} pg/mL é\n   positiva. Só os doentes entre esses valores são analisados aqui.\n2. **Modelo ({model}, escolhido no canto superior direito):** combina todas as variáveis numa pontuação entre 0 e 1. Os valores\n   em falta são tratados dentro das árvores (Random Forest, Extra Trees, Gradient Boosting) ou substituídos pela mediana\n   do treino mais um indicador "estava em falta" (Regressão Logística, SVM).\n3. **Limiares de segurança:** durante o treino cada doente recebe uma pontuação de validação cruzada (de modelos que\n   nunca o viram). A ferramenta encontra depois a pontuação mais baixa acima da qual pelo menos {ppv:.0%} dos doentes\n   tinham PL positiva (VPP) e a pontuação mais alta abaixo da qual pelo menos {npv:.0%} tinham PL negativa (VPN). {bound}\n4. **Tudo o que fica entre os limiares continua INCONCLUSIVO** e é referenciado para punção lombar, tal como antes.\n5. **Verificações de segurança:** os doentes fora da zona cinzenta não são classificados pelo modelo; valores implausíveis\n   (p. ex. hemoglobina = 45 g/dL) bloqueiam a classificação; doentes com sinal de alarme (características atípicas) ou com\n   mais de {miss:.0%} das variáveis em falta ficam inconclusivos.\n',
    'The default {model} model is {reason}: training it from {name} (about 1 minute, only once) ...':
        'O modelo padrão {model} {reason}: a treiná-lo a partir de {name} (cerca de 1 minuto, só uma vez) ...',
    "Trained models of this type found in the 'models' folder.":
        "Modelos treinados deste tipo encontrados na pasta 'models'.",
    "Your uploaded file, unchanged, with extra columns on each patient row: AI decision, model, score, explanation, missing variables and notes. A sheet 'AI prediction info' describes the model used.":
        "O ficheiro que carregou, sem alterações, com colunas extra em cada linha de doente: decisão, modelo, pontuação, explicação, variáveis em falta e notas. Uma folha 'Informação da previsão IA' descreve o modelo usado.",
    'Report of the **{model}** model `{name}` (change the model at the top right).':
        'Relatório do modelo **{model}** `{name}` (mude o modelo no canto superior direito).',
    "By default the shipped models of every type, all trained on the same dataset. To compare models on your own data, train them with 'Train every model type' in the Train model tab.":
        "Por omissão, os modelos fornecidos de cada tipo, todos treinados com o mesmo conjunto de dados. Para comparar modelos com os seus dados, treine-os com 'Treinar todos os tipos de modelo' no separador Treinar modelo.",
    'Select at least one model.':
        'Selecione pelo menos um modelo.',
    'Reference model for the paired differences':
        'Modelo de referência para as diferenças emparelhadas',
    '{model} saved to `models/{name}`: POSITIVE if score >= **{pos}**, NEGATIVE if score <= **{neg}**.':
        '{model} guardado em `models/{name}`: POSITIVO se pontuação >= **{pos}**, NEGATIVO se pontuação <= **{neg}**.',
    'Click **Use the new model now** (or select it in the sidebar) to classify patients with it; details are in **Model report** and **Compare models**.':
        'Clique em **Usar já o novo modelo** (ou selecione-o na barra lateral) para classificar doentes com ele; os detalhes estão em **Relatório do modelo** e **Comparar modelos**.',
    'Out-of-fold scores of the training patients, by LP result, with the three zones.':
        'Pontuações fora da partição dos doentes de treino, por resultado da PL, com as três zonas.',
    'LPs avoided, wrong calls, PPV and NPV come from nested cross-validation (patients never used to build or tune the model): this is the honest estimate for new patients. Brier score: mean squared error of the score as a probability (lower = better calibrated).':
        'PL evitadas, classificações erradas, VPP e VPN vêm da validação cruzada aninhada (doentes nunca usados para construir ou afinar o modelo): é a estimativa honesta para novos doentes. Score de Brier: erro quadrático médio da pontuação vista como probabilidade (mais baixo = melhor calibrado).',
    'Classify a file with every model':
        'Classificar um ficheiro com todos os modelos',
    '**How to read this page**\n\n- **LPs avoided** is what matters clinically: patients spared a lumbar puncture while every POSITIVE/NEGATIVE call stays within the safety rule.\n- Overlapping confidence intervals mean the models cannot be told apart with these patients.\n- A model can have a similar AUC but avoid fewer LPs: what counts is how many patients fall in the zones where the safety rule is proven.\n- Choosing the best of several models on the same data is slightly optimistic: confirm the choice on an independent cohort.':
        '**Como ler esta página**\n\n- **PL evitadas** é o que interessa clinicamente: doentes que dispensam a punção lombar mantendo todas as classificações POSITIVO/NEGATIVO dentro da regra de segurança.\n- Intervalos de confiança sobrepostos significam que os modelos não se distinguem com estes doentes.\n- Um modelo pode ter AUC semelhante e evitar menos PL: o que conta é quantos doentes caem nas zonas onde a regra de segurança está demonstrada.\n- Escolher o melhor de vários modelos nos mesmos dados é ligeiramente otimista: confirme a escolha numa coorte independente.',
    'Paired differences versus {model}':
        'Diferenças emparelhadas em relação a {model}',
    "Same patients, same folds; 95% bootstrap confidence intervals (1000 resamples). 'Significant' means the interval excludes zero.":
        "Mesmos doentes, mesmas partições; intervalos de confiança bootstrap a 95% (1000 reamostragens). 'Significativa' quer dizer que o intervalo não inclui o zero.",
    "These models were not trained on the same patients, so paired differences cannot be computed. Train them together with 'Train every model type'.":
        "Estes modelos não foram treinados com os mesmos doentes, por isso não é possível calcular diferenças emparelhadas. Treine-os juntos com 'Treinar todos os tipos de modelo'.",
    'The models agree on {p:.0%} of the patients.':
        'Os modelos concordam em {p:.0%} dos doentes.',
    'Download the comparison (Excel)':
        'Descarregar a comparação (Excel)',
    '_model_comparison':
        '_comparacao_modelos',

    # --- SHAP, decision curves, augmentation ----------------------------------------------------------
    'Training augmented with {k} literature-based synthetic patients ({file}); thresholds and validation use the {n} real patients only.':
        'Treino aumentado com {k} doentes sintéticos baseados na literatura ({file}); os limiares e a validação usam apenas os {n} doentes reais.',
    'LP for everyone':
        'PL para todos',
    'LP for no one':
        'PL para ninguém',
    'p-tau217 alone':
        'p-tau217 isolada',
    'Net benefit':
        'Benefício líquido',
    'Decision curves (cross-validated scores)':
        'Curvas de decisão (pontuações de validação cruzada)',
    'Net lumbar punctures avoided per 100 patients':
        'Punções lombares evitadas (líquidas) por 100 doentes',
    'net LPs avoided per 100':
        'PL evitadas líquidas por 100',
    'missing':
        'em falta',
    '{n} e4 allele(s)':
        '{n} alelo(s) e4',
    'Model score (dashed: average patient {b:.2f}; solid: this patient {s:.2f}; dotted: NEGATIVE / POSITIVE thresholds)':
        'Pontuação do modelo (tracejado: doente médio {b:.2f}; contínuo: este doente {s:.2f}; ponteado: limiares NEGATIVO / POSITIVO)',
    'Mean |SHAP| (average change of the score)':
        '|SHAP| médio (alteração média da pontuação)',
    'SHAP value per patient (red = high value of the variable, blue = low, grey = missing)':
        'Valor SHAP por doente (vermelho = valor alto da variável, azul = baixo, cinzento = em falta)',
    'What drives the {model} score (SHAP, {n} training patients)':
        'O que determina a pontuação do {model} (SHAP, {n} doentes de treino)',
    'Variable':
        'Variável',
    'Patient value':
        'Valor do doente',
    'Contribution to the score':
        'Contribuição para a pontuação',
    'Effect':
        'Efeito',
    'Average score (base)':
        'Pontuação média (base)',
    'Main factors':
        'Principais fatores',
    'raises the score (towards POSITIVE)':
        'aumenta a pontuação (para POSITIVO)',
    'lowers the score (towards NEGATIVE)':
        'diminui a pontuação (para NEGATIVO)',
    'no effect':
        'sem efeito',
    'Why this score? Explanation per patient (SHAP)':
        'Porquê esta pontuação? Explicação por doente (SHAP)',
    "SHAP values show how much each variable moved this patient's score away from the score of an average training patient. Positive values push towards POSITIVE, negative towards NEGATIVE. They explain the model, not the biology.":
        'Os valores SHAP mostram quanto cada variável afastou a pontuação deste doente da pontuação de um doente de treino médio. Valores positivos empurram para POSITIVO, negativos para NEGATIVO. Explicam o modelo, não a biologia.',
    "Average training patient: {b:.3f}  +  sum of the contributions: {s:+.3f}  =  this patient's score {score:.3f}.":
        'Doente de treino médio: {b:.3f}  +  soma das contribuições: {s:+.3f}  =  pontuação deste doente {score:.3f}.',
    'Compute explanations for all patients (Excel)':
        'Calcular as explicações de todos os doentes (Excel)',
    'This model file has no reference patients for explanations. Re-train it to enable SHAP.':
        'Este ficheiro de modelo não tem doentes de referência para as explicações. Volte a treiná-lo para ativar o SHAP.',
    'No patient received a model score (outside the grey zone or data problems).':
        'Nenhum doente recebeu pontuação do modelo (fora da zona cinzenta ou problemas nos dados).',
    'Download the explanations (Excel)':
        'Descarregar as explicações (Excel)',
    'Global explanation: what drives the score (SHAP)':
        'Explicação global: o que determina a pontuação (SHAP)',
    'Decision curve analysis':
        'Análise de curvas de decisão',
    'Computing the explanation ...':
        'A calcular a explicação ...',
    "Left: average size of each variable's effect on the score. Right: one dot per reference patient; dots to the right raised that patient's score. Colour = the variable's value (red high, blue low). Unlike permutation importance, this also shows the direction and the shape of each effect.":
        'Esquerda: tamanho médio do efeito de cada variável na pontuação. Direita: um ponto por doente de referência; pontos à direita aumentaram a pontuação desse doente. Cor = valor da variável (vermelho alto, azul baixo). Ao contrário da importância por permutação, mostra também o sentido e a forma de cada efeito.',
    'What does the decision curve show?':
        'O que mostra a curva de decisão?',
    '_shap_explanations':
        '_explicacoes_shap',
    'Computing SHAP values for the reference patients (once) ...':
        'A calcular os valores SHAP dos doentes de referência (só uma vez) ...',
    '**Decision curve analysis asks one question: if we act on this score, do patients gain more than they lose,\ncompared with simply doing a lumbar puncture in everyone?** AUC cannot answer it, because AUC ignores what a wrong\ndecision costs.\n\n- **Threshold probability (x-axis).** "I would keep the LP (treat the patient as possibly amyloid-positive) if the\n  probability of a positive LP is at least pt." Choosing pt is choosing an exchange rate: at pt = 0.10, missing one\n  amyloid-positive patient is judged as bad as 9 unnecessary LPs. This is the same trade-off as an NPV of 90 %\n  (dotted line).\n- **Net benefit (left).** True positives found per patient, minus false positives weighted by that exchange rate:\n  NB = TP/n - FP/n x pt/(1 - pt). It is expressed in "true positives per patient, net of harm". The curve of a useful\n  model lies above both reference lines: **LP for everyone** (today\'s practice in the grey zone) and **LP for no\n  one**.\n- **Net LPs avoided per 100 patients (right).** The clinically direct reading: how many lumbar punctures the score\n  saves per 100 grey-zone patients, after subtracting the amyloid-positive patients it would miss, valued at the\n  chosen exchange rate. 0 = no better than LP for everyone; negative = worse.\n- **How it complements the 90 % / 95 % rule.** The safety rule decides *which* patients get an answer. The decision\n  curve shows whether acting on the score is worthwhile across all reasonable trade-offs, and lets clinicians\n  choose their own trade-off. It uses each model\'s cross-validated scores as probabilities, so it also penalises\n  badly calibrated models.\n- Reference: Vickers & Elkin, *Med Decis Making* 2006; Vickers et al., *Diagn Progn Res* 2019. DCA is part of\n  the TRIPOD+AI reporting recommendations for clinical prediction models.\n':
        '**A análise de curvas de decisão responde a uma pergunta: se agirmos com base nesta pontuação, os doentes\nganham mais do que perdem, em comparação com fazer simplesmente punção lombar a todos?** A AUC não responde a isto,\nporque ignora o custo de uma decisão errada.\n\n- **Probabilidade limiar (eixo x).** "Mantinha a PL (tratava o doente como possivelmente amiloide-positivo) se a\n  probabilidade de PL positiva fosse pelo menos pt." Escolher pt é escolher uma taxa de troca: com pt = 0,10, falhar um\n  doente amiloide-positivo é considerado tão mau como 9 PL desnecessárias. É o mesmo compromisso que um VPN de 90 %\n  (linha ponteada).\n- **Benefício líquido (esquerda).** Verdadeiros positivos encontrados por doente, menos os falsos positivos pesados\n  por essa taxa de troca: BL = VP/n - FP/n x pt/(1 - pt). Exprime-se em "verdadeiros positivos por doente, líquidos de\n  dano". A curva de um modelo útil fica acima das duas linhas de referência: **PL para todos** (a prática atual na\n  zona cinzenta) e **PL para ninguém**.\n- **PL evitadas líquidas por 100 doentes (direita).** A leitura clínica direta: quantas punções lombares a pontuação\n  poupa por 100 doentes da zona cinzenta, depois de descontar os doentes amiloide-positivos que falharia, valorizados\n  à taxa de troca escolhida. 0 = não é melhor do que PL para todos; negativo = pior.\n- **Como complementa a regra dos 90 % / 95 %.** A regra de segurança decide *que* doentes recebem resposta. A curva de\n  decisão mostra se vale a pena agir com base na pontuação para todos os compromissos razoáveis, e deixa os clínicos\n  escolherem o seu. Usa as pontuações de validação cruzada de cada modelo como probabilidades, por isso também\n  penaliza modelos mal calibrados.\n- Referências: Vickers & Elkin, *Med Decis Making* 2006; Vickers et al., *Diagn Progn Res* 2019. A análise de curvas\n  de decisão faz parte das recomendações TRIPOD+AI para modelos de predição clínica.\n',
    'No threshold could be certified with this training data (PPV/NPV >= {ppv:.0%} / {npv:.0%} with {conf:.0%} confidence): every grey-zone patient will be INCONCLUSIVE. More patients or more informative variables are needed; the scores, SHAP explanations and decision curves still show what the model has learnt.':
        'Não foi possível certificar nenhum limiar com estes dados de treino (VPP/VPN >= {ppv:.0%} / {npv:.0%} com {conf:.0%} de confiança): todos os doentes da zona cinzenta ficarão INCONCLUSIVOS. São precisos mais doentes ou variáveis mais informativas; as pontuações, as explicações SHAP e as curvas de decisão continuam a mostrar o que o modelo aprendeu.',
    'Threshold probability pt':
        'Probabilidade limiar pt',
    "Net LPs avoided vs 'LP for everyone'":
        "PL evitadas líquidas face a 'PL para todos'",
    'Dotted line: pt = 1 - NPV target ({pt:.2f}): missing one amyloid-positive patient counts as much as {k:.0f} unnecessary LPs.':
        'Linha ponteada: pt = 1 - VPN alvo ({pt:.2f}): falhar um doente amiloide-positivo conta tanto como {k:.0f} PL desnecessárias.',
}
