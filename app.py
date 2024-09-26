import streamlit as st
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Carrega as variáveis de ambiente
load_dotenv()

# Configura o cliente Anthropic com LangChain
llm = ChatAnthropic(model="claude-3-sonnet-20240229", anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

# Inicializa as variáveis de estado
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'score' not in st.session_state:
    st.session_state.score = 0

# Template para gerar perguntas
question_template = PromptTemplate(
    input_variables=["previous_answers"],
    template="""
    Você é um entrevistador especializado em avaliar empreendedores de startups.
    Gere uma pergunta de múltipla escolha em português para avaliar as habilidades empreendedoras do candidato.
    A pergunta deve ser relevante considerando as respostas anteriores: {previous_answers}
    
    Formato da resposta:
    Pergunta: [Insira a pergunta aqui]
    A) [Opção A]
    B) [Opção B]
    C) [Opção C]
    D) [Opção D]

    Certifique-se de que a pergunta e cada opção estejam em linhas separadas, exatamente como mostrado acima.
    """
)

# Template para avaliar respostas
evaluation_template = PromptTemplate(
    input_variables=["question", "answer"],
    template="""
    Avalie a resposta do candidato para a seguinte pergunta:
    
    {question}
    
    Resposta do candidato: {answer}
    
    Dê uma pontuação de 0 a 10 para esta resposta, considerando o potencial empreendedor do candidato.
    Formato da resposta: [X] onde X é a pontuação numérica.
    Em seguida, você pode adicionar uma breve justificativa para a pontuação.
    
    Exemplo de resposta:
    [8]
    O candidato demonstrou boa compreensão dos desafios empreendedores...
    """
)

# Cria as chains
question_chain = LLMChain(llm=llm, prompt=question_template)
evaluation_chain = LLMChain(llm=llm, prompt=evaluation_template)

# Função para gerar uma nova pergunta
def generate_question():
    try:
        result = question_chain.run(previous_answers=st.session_state.answers)
        return result
    except Exception as e:
        st.error(f"""
        Ops! Parece que houve um problema ao gerar a próxima pergunta.
        
        Mensagem amigável: Estamos enfrentando algumas dificuldades técnicas no momento. 
        Isso pode ser devido a um problema com a conexão à API ou com os créditos disponíveis. 
        Por favor, tente novamente mais tarde ou entre em contato com o suporte se o problema persistir.
        
        Detalhes técnicos: {str(e)}
        """)
        st.stop()

# Função para avaliar a resposta e gerar uma pontuação
def evaluate_answer(question, answer):
    try:
        result = evaluation_chain.run(question=question, answer=answer)
        # Extrair apenas o número da resposta
        score = result.strip().split('[')[1].split(']')[0]
        return float(score)
    except Exception as e:
        st.error(f"""
        Ops! Ocorreu um erro ao avaliar sua resposta.
        
        Mensagem amigável: Estamos com dificuldades para processar sua resposta no momento.
        Por favor, tente novamente em alguns instantes ou contate o suporte se o problema continuar.
        
        Detalhes técnicos: {str(e)}
        """)
        return 0  # Retorna 0 pontos em caso de erro

# Configuração da página Streamlit
st.set_page_config(page_title="Entrevista para Empreendedores", page_icon="🚀", layout="centered")

# Título e introdução
st.title("🚀 Avaliação de Potencial Empreendedor")
st.markdown("""
    Bem-vindo à nossa entrevista virtual para avaliar seu potencial como empreendedor de startups!
    Responda às perguntas de múltipla escolha e descubra sua pontuação no final.
""")

# Loop principal da entrevista
if st.session_state.current_question < 10:
    if len(st.session_state.questions) <= st.session_state.current_question:
        with st.spinner("Gerando próxima pergunta..."):
            new_question = generate_question()
            st.session_state.questions.append(new_question)
    
    question_full = st.session_state.questions[st.session_state.current_question]
    question_parts = question_full.split('\n')
    question = next((part for part in question_parts if part.startswith("Pergunta:")), "")
    question = question.replace('Pergunta:', '').strip()
    options = [part.strip() for part in question_parts if part.strip().startswith(('A)', 'B)', 'C)', 'D)'))]
    
    st.markdown(f"### Pergunta {st.session_state.current_question + 1}")
    st.write(question)
    
    # Criar botões para as opções de resposta
    if options:
        cols = st.columns(2)
        for i, option in enumerate(options):
            option_parts = option.split(')', 1)
            if len(option_parts) == 2:
                option_letter, option_text = option_parts
                if cols[i % 2].button(f"{option_letter.strip()}) {option_text.strip()}", key=f"q{st.session_state.current_question}_opt{i}"):
                    st.session_state.answers.append(option)
                    with st.spinner("Avaliando resposta..."):
                        score = evaluate_answer(question_full, option)
                        st.session_state.score += score
                    st.session_state.current_question += 1
                    st.rerun()
            else:
                st.error(f"Formato de opção inválido: {option}")
    else:
        st.error("Nenhuma opção válida encontrada na resposta do modelo.")

# Exibir resultado final
if st.session_state.current_question == 10:
    final_score = st.session_state.score / 10
    st.markdown(f"## Sua pontuação final: {final_score:.2f} / 10")
    
    if final_score >= 8:
        st.success("Parabéns! Você demonstra um excelente potencial empreendedor!")
    elif final_score >= 6:
        st.info("Você tem um bom potencial empreendedor. Continue desenvolvendo suas habilidades!")
    else:
        st.warning("Você pode precisar desenvolver mais suas habilidades empreendedoras. Não desista!")
    
    if st.button("Reiniciar entrevista"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# Barra de progresso
st.progress(st.session_state.current_question / 10)

# Rodapé
st.markdown("---")
st.markdown("Desenvolvido com ❤️ usando Streamlit, LangChain e Anthropic AI")