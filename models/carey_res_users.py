# pos_carey/models/carey_res_users.py
from odoo import api, fields, models
from odoo.exceptions import ValidationError

GROUP_OPERATOR = "pos_carey.group_pos_branch_operator"
GROUP_MANAGER = "pos_carey.group_pos_branch_manager"


class ResUsers(models.Model):
    _inherit = "res.users"

    pos_operator_branch_id = fields.Many2one(
        comodel_name="pos.config",
        string="Sucursal asignada",
        ondelete="restrict",
        help="Sucursal en la que opera el usuario. Determina qué fichas de "
             "cliente puede ver, editar y crear.",
    )

    pos_carey_access_level = fields.Selection(
        selection=[
            ("none", "Ninguno"),
            ("operator", "Operador de Sucursal"),
            ("manager", "Gerencia Global"),
        ],
        string="Acceso por sucursal",
        default="none",
        help="Determina si el usuario administra clientes de una sola "
             "sucursal o tiene acceso global de gerencia.",
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["pos_operator_branch_id"]

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._sync_pos_carey_groups()
        return users

    def write(self, vals):
        result = super().write(vals)
        if "pos_carey_access_level" in vals:
            self._sync_pos_carey_groups()
        return result

    def _sync_pos_carey_groups(self):
        """Traduce la selección a membresía real de grupo. Se ejecuta
        DESPUÉS del write principal, con super() para no reentrar en
        este mismo override y evitar recursión."""
        group_operator = self.env.ref(GROUP_OPERATOR)
        group_manager = self.env.ref(GROUP_MANAGER)
        for user in self:
            commands = [(3, group_operator.id), (3, group_manager.id)]
            if user.pos_carey_access_level == "operator":
                commands.append((4, group_operator.id))
            elif user.pos_carey_access_level == "manager":
                commands.append((4, group_manager.id))
            super(ResUsers, user).write({"group_ids": commands})

    @api.constrains("pos_operator_branch_id", "pos_carey_access_level")
    def _check_operator_branch_required(self):
        for user in self:
            if user.pos_carey_access_level == "operator" and not user.pos_operator_branch_id:
                raise ValidationError(
                    "El usuario «%s» está configurado como Operador de "
                    "Sucursal, por lo que debe tener una sucursal asignada."
                    % user.name
                )