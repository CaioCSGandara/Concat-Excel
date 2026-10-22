Sistema de importação de dados xlsx

Criaremos um sistema para concatenar dados de arquivos xlsx. A ideia é resolver o seguinte problema:
Um amigo, todos os dias, recebe uma planilha de um cliente. Ele precisa fazer com que os dados dessa planilha sejam inseridos em uma planilha mestre. Atualmente, isso está sendo feito manualmente, e leva muito tempo.

A ideia é criar um sistema bem simples em python e empacotar em um exe. Todos os dados serão salvos localmente mesmo, no computador dele.

Os requisitos funcionais são:

1. Selecionar a planilha mestre no sistema de arquivos. Quando ele abrir o programa, independente de te-lo fechado, desligado o pc ou qualquer coisa, o programa deve lembrar de qual planilha é a mestre. Ele pode altera-la, se quiser. 

2. Selecionar a planilha de onde os dados serão importados (planilha fonte) para a planilha mestre. Essa não deve ficar salva: sempre que ele abrir o programa ou finalizar alguma importação, o usuário terá que escolher essa planilha novamente. 

3. Selecionar o mapeamento entre colunas. Deve ser possível criar, editar e deletar mapeamentos.

4. Após ter selecionado a planilha mestre, a planilha fonte e o mapeamento, o sistema deve, antes de tudo, criar uma cópia da planilha mestre em um diretório específico de backup. 

5. Se o backup falhar, uma mensagem é exibida informando o usuário, e o procedimento é cancelado.

6. Se o backup for bem sucedido, as linhas da planilha fonte devem ser concatenadas com as linhas da planilha mestre, respeitando o mapeamento de colunas, fazendo com que, DE FORMA ALGUMA, algum dado seja perdido ou sobrescrito. 

7. Durante o procedimento, deve haver uma barra de progresso, para que o usuário tenha noção de quanto tempo falta para o procedimento ser concluído. Juntamente com esse progresso, devem ser exibidos logs de importação, mostrando os registros que estão sendo importados. Se algum existir alguma falha, como por exemplo mapeamento inconsistente (principalmente esse), o problema deve ser registrado no log, e o procedimento deve ser cancelado.

8. Se todos os dados forem importados corretamente, a planilha mestre deve ser salva, e uma mensagem exibida.


Stack:
pandas, openpyxl, customtkinter, pyinstaller

Faça uma interface moderna e intuitiva, com um suporte a modo light e dark.

Regras de qualidade de código:

1. Seguir os padrões do PEP8.
2. O código deve ser modular e organizado em classes e funções.
3. O código deve ser documentado com docstrings.
4. O código deve ser testável.
5. O código deve ser seguro.
6. O código deve ser eficiente.
7. O código deve ser manutenível.
8. O código deve ser legível.
9. O código deve ser escalável.
10. O código deve ser reutilizável.
11. Deve ser utilziado o padrão de nomenclatura snack_case.
12. Usar tipagem FORTE (nunca usar any).

O que está em aberto: 

O salvamento dos dados (mapeando, path/nome da planilha mestre, e outros dados necessários) sempre será local. A questão é: em que tipo de arquivo? json? yaml? csv? Faça uma análise sobre isso antes de começar. Se tiver alguma dúvida ou sugestão, também me mande antes de começar.
