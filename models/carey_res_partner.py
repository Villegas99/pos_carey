from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

GROUP_OPERATOR = "pos_carey.group_pos_branch_operator"
GROUP_MANAGER = "pos_carey.group_pos_branch_manager"
GROUP_SYSTEM = "base.group_system"


class ResPartner(models.Model):
    _inherit = "res.partner"

    pos_branch_id = fields.Many2one(
        comodel_name="pos.config",
        string="Sucursal",
        index=True,
        ondelete="restrict",
        default=lambda self: self.env.user.pos_operator_branch_id.id,
        help="Sucursal propietaria del cliente. Vacío significa cliente global, "
             "visible para todas las sucursales.",
    )
    pos_branch_editable = fields.Boolean(
        string="Sucursal editable",
        compute="_compute_pos_branch_editable",
        help="Técnico: controla si el campo Sucursal es modificable en la vista.",
    )

    @api.depends_context("uid")
    def _compute_pos_branch_editable(self):
        editable = self.env.user.has_group(GROUP_MANAGER) or self.env.user.has_group(
            GROUP_SYSTEM
        )
        for partner in self:
            partner.pos_branch_editable = editable

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _is_restricted_operator(self):
        """El usuario actual está sujeto al aislamiento por sucursal."""
        user = self.env.user
        if user.has_group(GROUP_MANAGER) or user.has_group(GROUP_SYSTEM):
            return False
        return user.has_group(GROUP_OPERATOR)

    def _check_branch_assignment(self, values):
        """Impide que un operador asigne un cliente fuera de su sucursal."""
        if "pos_branch_id" not in values or not self._is_restricted_operator():
            return
        user_branch = self.env.user.pos_operator_branch_id
        if values["pos_branch_id"] != user_branch.id:
            raise UserError(
                "Solo puede asignar clientes a su propia sucursal (%s). "
                "No puede crear ni liberar clientes globales, ni moverlos a "
                "otra sucursal." % (user_branch.display_name or "sin asignar")
            )

    def _branch_from_parent(self, values):
        """Un contacto hijo hereda siempre la sucursal de su empresa padre."""
        if "parent_id" not in values:
            return
        if values["parent_id"]:
            parent = self.browse(values["parent_id"])
            values["pos_branch_id"] = parent.pos_branch_id.id

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            self._branch_from_parent(values)
            self._check_branch_assignment(values)
        return super().create(vals_list)

    def write(self, values):
        self._branch_from_parent(values)
        self._check_branch_assignment(values)
        result = super().write(values)
        if "pos_branch_id" in values:
            children = self.child_ids.filtered(
                lambda child: child.pos_branch_id.id != values["pos_branch_id"]
            )
            if children:
                children.write({"pos_branch_id": values["pos_branch_id"]})
        return result

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("pos_branch_id", "parent_id")
    def _check_branch_hierarchy(self):
        for partner in self:
            parent = partner.parent_id
            if parent and partner.pos_branch_id != parent.pos_branch_id:
                raise ValidationError(
                    "El contacto «%s» debe pertenecer a la misma sucursal que su "
                    "empresa matriz «%s» (%s)."
                    % (
                        partner.display_name,
                        parent.display_name,
                        parent.pos_branch_id.display_name or "Global",
                    )
                )