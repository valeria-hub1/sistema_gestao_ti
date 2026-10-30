from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from sqlalchemy.orm import joinedload

from models.conexao import engine, SessionLocal, Base
from models.equipamento_model import Equipamento
from models.suporte_model import Suporte


# ==========================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ==========================================

app = Flask(__name__)
app.secret_key = "gestao_ti_chave_local"

# Cria as tabelas caso ainda não existam.
Base.metadata.create_all(bind=engine)


# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def converter_data(valor):
    """Converte uma data do formulário para o formato date."""
    if not valor:
        return None

    return datetime.strptime(valor, "%Y-%m-%d").date()


def converter_custo(valor):
    """Converte o custo informado no formulário para número."""
    if not valor:
        return 0.0

    return float(valor.replace(",", "."))


def buscar_equipamentos(db):
    """Retorna os equipamentos em ordem de patrimônio."""
    return db.query(Equipamento).order_by(
        Equipamento.patrimonio
    ).all()


# ==========================================
# PÁGINA INICIAL
# ==========================================

@app.route("/")
def inicio():
    db = SessionLocal()

    try:
        total_equipamentos = db.query(Equipamento).count()

        em_uso = db.query(Equipamento).filter(
            Equipamento.status == "Em Uso"
        ).count()

        manutencao = db.query(Equipamento).filter(
            Equipamento.status == "Em Manutenção"
        ).count()

        total_suportes = db.query(Suporte).count()

        return render_template(
            "index.html",
            equipamentos=total_equipamentos,
            em_uso=em_uso,
            manutencao=manutencao,
            suportes=total_suportes,
        )

    except Exception as erro:
        app.logger.exception("Erro ao carregar a página inicial.")
        flash("Não foi possível carregar o painel inicial.", "error")

        return render_template(
            "index.html",
            equipamentos=0,
            em_uso=0,
            manutencao=0,
            suportes=0,
        )

    finally:
        db.close()


# ==========================================
# LISTAR EQUIPAMENTOS
# ==========================================

@app.route("/equipamentos")
def listar_equipamentos():
    db = SessionLocal()

    try:
        lista = db.query(Equipamento).order_by(
            Equipamento.id.desc()
        ).all()

        return render_template(
            "equipamentos.html",
            equipamentos=lista,
        )

    except Exception:
        app.logger.exception("Erro ao listar equipamentos.")
        flash("Não foi possível carregar os equipamentos.", "error")
        return redirect(url_for("inicio"))

    finally:
        db.close()


# ==========================================
# CADASTRAR EQUIPAMENTO
# ==========================================

@app.route("/equipamentos/novo", methods=["GET", "POST"])
def novo_equipamento():
    db = SessionLocal()

    try:
        if request.method == "POST":

            patrimonio = request.form.get(
                "patrimonio", ""
            ).strip()

            if not patrimonio:
                flash("Informe o patrimônio do equipamento.", "error")

                return render_template(
                    "equipamento_form.html",
                    equipamento=None,
                )

            existente = db.query(Equipamento).filter(
                Equipamento.patrimonio == patrimonio
            ).first()

            if existente:
                flash("Esse patrimônio já está cadastrado.", "error")

                return render_template(
                    "equipamento_form.html",
                    equipamento=None,
                )

            equipamento = Equipamento(
                patrimonio=patrimonio,
                tipo=request.form.get("tipo", "").strip(),
                marca=request.form.get("marca", "").strip(),
                modelo=request.form.get("modelo", "").strip(),
                numero_serie=request.form.get(
                    "numero_serie", ""
                ).strip(),
                data_aquisicao=converter_data(
                    request.form.get("data_aquisicao", "")
                ),
                localizacao=request.form.get(
                    "localizacao", ""
                ).strip(),
                status=request.form.get("status", "Em Uso"),
            )

            db.add(equipamento)
            db.commit()

            flash("Equipamento cadastrado com sucesso!", "success")

            return redirect(url_for("listar_equipamentos"))

        return render_template(
            "equipamento_form.html",
            equipamento=None,
        )

    except Exception:
        db.rollback()
        app.logger.exception("Erro ao cadastrar equipamento.")
        flash(
            "Não foi possível cadastrar o equipamento. Verifique os dados.",
            "error",
        )

        return render_template(
            "equipamento_form.html",
            equipamento=None,
        )

    finally:
        db.close()


# ==========================================
# DETALHES DO EQUIPAMENTO
# ==========================================

@app.route("/equipamentos/<int:id>")
def detalhe_equipamento(id):
    db = SessionLocal()

    try:
        equipamento = db.query(Equipamento).filter(
            Equipamento.id == id
        ).first()

        if equipamento is None:
            flash("Equipamento não encontrado.", "error")
            return redirect(url_for("listar_equipamentos"))

        lista_suportes = db.query(Suporte).filter(
            Suporte.id_equipamento == id
        ).order_by(
            Suporte.id.desc()
        ).all()

        return render_template(
            "equipamento_detalhe.html",
            equipamento=equipamento,
            suportes=lista_suportes,
        )

    except Exception:
        app.logger.exception("Erro ao consultar equipamento.")
        flash("Não foi possível consultar o equipamento.", "error")
        return redirect(url_for("listar_equipamentos"))

    finally:
        db.close()


# ==========================================
# EDITAR EQUIPAMENTO
# ==========================================

@app.route(
    "/equipamentos/<int:id>/editar",
    methods=["GET", "POST"]
)
def editar_equipamento(id):
    db = SessionLocal()

    try:
        equipamento = db.query(Equipamento).filter(
            Equipamento.id == id
        ).first()

        if equipamento is None:
            flash("Equipamento não encontrado.", "error")
            return redirect(url_for("listar_equipamentos"))

        if request.method == "POST":

            patrimonio = request.form.get(
                "patrimonio", ""
            ).strip()

            if not patrimonio:
                flash("Informe o patrimônio do equipamento.", "error")

                return render_template(
                    "equipamento_form.html",
                    equipamento=equipamento,
                )

            duplicado = db.query(Equipamento).filter(
                Equipamento.patrimonio == patrimonio,
                Equipamento.id != id,
            ).first()

            if duplicado:
                flash(
                    "Esse patrimônio já pertence a outro equipamento.",
                    "error",
                )

                return render_template(
                    "equipamento_form.html",
                    equipamento=equipamento,
                )

            equipamento.patrimonio = patrimonio
            equipamento.tipo = request.form.get("tipo", "").strip()
            equipamento.marca = request.form.get("marca", "").strip()
            equipamento.modelo = request.form.get("modelo", "").strip()

            equipamento.numero_serie = request.form.get(
                "numero_serie", ""
            ).strip()

            equipamento.data_aquisicao = converter_data(
                request.form.get("data_aquisicao", "")
            )

            equipamento.localizacao = request.form.get(
                "localizacao", ""
            ).strip()

            equipamento.status = request.form.get(
                "status", "Em Uso"
            )

            db.commit()

            flash("Equipamento atualizado com sucesso!", "success")

            return redirect(
                url_for("detalhe_equipamento", id=id)
            )

        return render_template(
            "equipamento_form.html",
            equipamento=equipamento,
        )

    except Exception:
        db.rollback()
        app.logger.exception("Erro ao editar equipamento.")
        flash("Não foi possível atualizar o equipamento.", "error")

        return redirect(url_for("listar_equipamentos"))

    finally:
        db.close()


# ==========================================
# LISTAR REGISTROS DE SUPORTE
# ==========================================

@app.route("/suportes")
def suportes():
    db = SessionLocal()

    try:
        lista = (
            db.query(Suporte)
            .options(joinedload(Suporte.equipamento))
            .order_by(Suporte.id.desc())
            .all()
        )

        return render_template(
            "suportes.html",
            suportes=lista,
        )

    except Exception:
        app.logger.exception("Erro ao listar suportes.")
        flash("Não foi possível carregar os registros de suporte.", "error")
        return redirect(url_for("inicio"))

    finally:
        db.close()


# ==========================================
# CADASTRAR SUPORTE
# ==========================================

@app.route("/suportes/novo", methods=["GET", "POST"])
def novo_suporte():
    db = SessionLocal()

    try:
        equipamentos = buscar_equipamentos(db)

        if request.method == "POST":

            id_equipamento = request.form.get(
                "id_equipamento", ""
            )

            if not id_equipamento:
                flash("Selecione um equipamento.", "error")

                return render_template(
                    "suporte_form.html",
                    equipamentos=equipamentos,
                    suporte=None,
                )

            equipamento = db.query(Equipamento).filter(
                Equipamento.id == int(id_equipamento)
            ).first()

            if equipamento is None:
                flash("O equipamento selecionado não existe.", "error")

                return render_template(
                    "suporte_form.html",
                    equipamentos=equipamentos,
                    suporte=None,
                )

            suporte = Suporte(
                id_equipamento=int(id_equipamento),
                data_suporte=converter_data(
                    request.form.get("data_suporte", "")
                ),
                tipo_suporte=request.form.get(
                    "tipo_suporte", ""
                ).strip(),
                descricao=request.form.get(
                    "descricao", ""
                ).strip(),
                responsavel=request.form.get(
                    "responsavel", ""
                ).strip(),
                custo=converter_custo(
                    request.form.get("custo", "")
                ),
            )

            db.add(suporte)
            db.commit()

            flash("Registro de suporte cadastrado com sucesso!", "success")

            return redirect(url_for("suportes"))

        return render_template(
            "suporte_form.html",
            equipamentos=equipamentos,
            suporte=None,
        )

    except Exception:
        db.rollback()
        app.logger.exception("Erro ao cadastrar suporte.")
        flash(
            "Não foi possível cadastrar o suporte. Verifique os dados.",
            "error",
        )

        return render_template(
            "suporte_form.html",
            equipamentos=buscar_equipamentos(db),
            suporte=None,
        )

    finally:
        db.close()


# ==========================================
# EDITAR SUPORTE
# ==========================================

@app.route(
    "/suportes/<int:id>/editar",
    methods=["GET", "POST"]
)
def editar_suporte(id):
    db = SessionLocal()

    try:
        suporte = (
            db.query(Suporte)
            .options(joinedload(Suporte.equipamento))
            .filter(Suporte.id == id)
            .first()
        )

        if suporte is None:
            flash("Registro de suporte não encontrado.", "error")
            return redirect(url_for("suportes"))

        equipamentos = buscar_equipamentos(db)

        if request.method == "POST":

            id_equipamento = request.form.get(
                "id_equipamento", ""
            )

            if not id_equipamento:
                flash("Selecione um equipamento.", "error")

                return render_template(
                    "suporte_form.html",
                    equipamentos=equipamentos,
                    suporte=suporte,
                )

            equipamento = db.query(Equipamento).filter(
                Equipamento.id == int(id_equipamento)
            ).first()

            if equipamento is None:
                flash("O equipamento selecionado não existe.", "error")

                return render_template(
                    "suporte_form.html",
                    equipamentos=equipamentos,
                    suporte=suporte,
                )

            suporte.id_equipamento = int(id_equipamento)

            suporte.data_suporte = converter_data(
                request.form.get("data_suporte", "")
            )

            suporte.tipo_suporte = request.form.get(
                "tipo_suporte", ""
            ).strip()

            suporte.descricao = request.form.get(
                "descricao", ""
            ).strip()

            suporte.responsavel = request.form.get(
                "responsavel", ""
            ).strip()

            suporte.custo = converter_custo(
                request.form.get("custo", "")
            )

            db.commit()

            flash("Registro de suporte atualizado com sucesso!", "success")

            return redirect(url_for("suportes"))

        return render_template(
            "suporte_form.html",
            equipamentos=equipamentos,
            suporte=suporte,
        )

    except Exception:
        db.rollback()
        app.logger.exception("Erro ao editar suporte.")
        flash("Não foi possível atualizar o registro de suporte.", "error")

        return redirect(url_for("suportes"))

    finally:
        db.close()


# ==========================================
# EXCLUIR SUPORTE
# ==========================================

@app.route("/suportes/<int:id>/excluir", methods=["POST"])
def excluir_suporte(id):
    db = SessionLocal()

    try:
        suporte = db.query(Suporte).filter(
            Suporte.id == id
        ).first()

        if suporte is None:
            flash("Registro de suporte não encontrado.", "error")

        else:
            db.delete(suporte)
            db.commit()

            flash("Registro de suporte excluído com sucesso!", "success")

        return redirect(url_for("suportes"))

    except Exception:
        db.rollback()
        app.logger.exception("Erro ao excluir suporte.")
        flash("Não foi possível excluir o registro de suporte.", "error")

        return redirect(url_for("suportes"))

    finally:
        db.close()


# ==========================================
# RELATÓRIOS
# ==========================================

@app.route("/relatorios")
def relatorios():
    db = SessionLocal()

    try:
        equipamentos = buscar_equipamentos(db)

        lista_suportes = (
            db.query(Suporte)
            .options(joinedload(Suporte.equipamento))
            .order_by(Suporte.id.desc())
            .all()
        )

        total_equipamentos = len(equipamentos)
        total_suportes = len(lista_suportes)

        custo_total = sum(
            float(suporte.custo or 0)
            for suporte in lista_suportes
        )

        return render_template(
            "relatorios.html",
            equipamentos=equipamentos,
            suportes=lista_suportes,
            total_equipamentos=total_equipamentos,
            total_suportes=total_suportes,
            custo_total=custo_total,
        )

    except Exception:
        app.logger.exception("Erro ao gerar relatórios.")
        flash("Não foi possível gerar os relatórios.", "error")
        return redirect(url_for("inicio"))

    finally:
        db.close()


# ==========================================
# SOBRE O SISTEMA
# ==========================================

@app.route("/sobre")
def sobre():
    return render_template("sobre.html")


# ==========================================
# EXECUTAR A APLICAÇÃO
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)

