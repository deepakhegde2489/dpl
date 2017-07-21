
from odoo import exceptions, _
from odoo import _, api, fields, models

class dpl_betting(models.Model):
    _name = 'dpl.betting'
    _description = 'betting'

    @api.onchange('match')
    def _onchange_match(self):
        participants = ['1', '2', '3']
        match = self.env['dpl.match'].search([('id', '=', self.match.id)]).id
        participant_1 = self.env['dpl.match'].search([('id', '=', match)]).participant_1.name
        participant_2 = self.env['dpl.match'].search([('id', '=', match)]).participant_2.name
        participants[0] = participant_1
        participants[1] = participant_2
        match = self.env['dpl.match'].search([('winner', '=', None)]).ids
        return {'domain': {'bet_on': [('name', 'in', participants)],'name': [('name', 'not in', participants)],
                                                                             'match': [('id', 'in', match)]}}

    name = fields.Many2one('dpl.participants',required=True,string="Bet by",domain="[('match_type', '=', 'singles')]")
    amount = fields.Integer('Bet Amount')
    match = fields.Many2one("dpl.match",string="On Match")
    bet_on = fields.Many2one('dpl.participants',string="Bet On",change_default=False)
    amount_won = fields.Float('Amount won')

    _sql_constraints = [
        ('name_match_uniq', 'unique(match, name)', 'Participant has already bet on this match!! '),
    ]

    @api.model
    def create(self,vals):
        if vals['amount'] % 20 != 0 or vals['amount']==0:
            raise exceptions.UserError(("Bet amount should be in multiples of 20"))
        else:
            return super(dpl_betting, self).create(vals)

    @api.one
    def write(self, vals):
        if vals['amount'] % 20 != 0:
            raise exceptions.UserError(("Bet amount should be in multiples of 20"))
        else:
            return super(dpl_betting, self).write(vals)

class dpl_match(models.Model):
    _name = 'dpl.match'
    _description = 'match'

    @api.one
    def match_name(self):
        self.name = str(self.participant_1.name) + " Vs " + str(self.participant_2.name)
        return None

    @api.onchange('participant_1')
    def _onchange_participant_1(self):
        participants = ['1', '2', '3']
        participants[0] = self.participant_1.name
        participants[1] = self.participant_2.name
        # match_onchange = self.env['dpl.match'].search(['|', ('participant_1', '=', self.participant_1.id), ('participant_2', '=', self.participant_2.id)])
        # if match_onchange.winner:
        #     raise exceptions.UserError(("Participant already set"))
        return {'domain': {'winner': [('name', 'in', participants)],'participant_2': [('id', '!=', self.participant_1.id)]}}

    @api.onchange('participant_2')
    def _onchange_participant_2(self):
        participants = ['1', '2', '3']
        participants[0] = self.participant_1.name
        participants[1] = self.participant_2.name
        # match_onchange = self.env['dpl.match'].search(['|',('participant_1', '=', self.participant_1.id), ('participant_2', '=', self.participant_2.id)])
        # if match_onchange.winner:
        #     raise exceptions.UserError(("Participant already set"))
        return {'domain': {'winner': [('name', 'in', participants)],'participant_1': [('id', '!=', self.participant_2.id)]}}

    @api.one
    def write(self, vals):
        match_id = self.env['dpl.match'].search([('participant_1', '=', self.participant_1.id),('participant_2', '=', self.participant_2.id)]).id
        match_onchange = self.env['dpl.match'].search([('participant_1', '=', self.participant_1.id), ('participant_2', '=', self.participant_2.id)])
        if match_onchange.winner:
            raise exceptions.UserError(("Participant already set"))

        bet_obj = self.env['dpl.betting'].search([('match', '=', match_id)])
        res = {}
        total = 0.0
        for amount in bet_obj:
            total += amount.amount
            res[amount] = total

        participant = self.env['dpl.participants'].search([('id', '=', vals['winner'])]).id
        bet_obj_won = self.env['dpl.betting'].search([('bet_on', '=', participant),('match', '=', match_id)])

        if self.participant_1.id != vals['winner']:
            looser_id = self.participant_1.id
        else:
            looser_id = self.participant_2.id
        bet_obj_looser = self.env['dpl.betting'].search([('bet_on', '=', looser_id), ('match', '=', match_id)])

        # no bet on other participant other than winner
        if bet_obj_won.ids.__len__() != 0 and bet_obj_looser.ids.__len__() == 0:
            i=0
            if self.participant_1.id == vals['winner']:
                winner_id = self.participant_1.id
            else:
                winner_id = self.participant_2.id

            participant_loose = self.env['dpl.participants'].search([('id', '=', winner_id)]).id
            match_id2 = self.env['dpl.match'].search([('participant_1', '=', self.participant_1.id), ('participant_2', '=', self.participant_2.id)]).id
            bet_obj_winner = self.env['dpl.betting'].search([('bet_on', '=', participant_loose), ('match', '=', match_id2)])

            for amount in bet_obj_winner:
                bet_by4 = self.env['dpl.betting'].search([('id', '=', bet_obj_winner.ids[i])])
                participant_id = self.env['dpl.participants'].search([('id', '=', bet_by4.name.id)]).id
                settlement_amount1 = amount.amount
                self._cr.execute(" UPDATE dpl_participants SET balance_amount = balance_amount + %s WHERE id=%s",
                                 (settlement_amount1, participant_id,))
                self._cr.execute(" UPDATE dpl_betting SET amount_won =  %s WHERE id=%s",
                                 (settlement_amount1, bet_by4.id,))

                i = i + 1

        elif bet_obj_won.ids.__len__() == 0 and bet_obj_looser.ids.__len__() != 0:
            if self.participant_1.id != vals['winner']:
                looser_id = self.participant_1.id
            else:
                looser_id = self.participant_2.id

            participant2 = self.env['dpl.participants'].search([('id', '=', looser_id)]).id
            bet_obj_won2 = self.env['dpl.betting'].search([('bet_on', '=', participant2),('match', '=', match_id)])
            i2 = 0
            for amount in bet_obj_won2:
                bet_by2 = self.env['dpl.betting'].search([('id', '=', bet_obj_won2.ids[i2])])
                participant_id = self.env['dpl.participants'].search([('id', '=', bet_by2.name.id)]).id
                bal2 = amount.amount
                # bal2 = - bal2
                self._cr.execute("UPDATE dpl_participants SET balance_amount = balance_amount + %s WHERE id=%s",(bal2,participant_id,))
                self._cr.execute(" UPDATE dpl_betting SET amount_won =  %s WHERE id=%s",
                                 (bal2, bet_by2.id,))
                i2 = i2 + 1
        else:
            #  bet on both participant
            res2 = {}
            total2 = 0.0
            count = 0
            # amount = 0
            for amount in bet_obj_won:
                total2 += amount.amount
                count += 1
                res2[amount] = total2

            slab = total2 / 20
            total_amount_to_be_shared = total - total2
            if slab != 0:
                amount_shared = total_amount_to_be_shared / slab
            else:
                amount_shared = 0
            participant = self.env['dpl.participants'].search([('id', '=', vals['winner'])]).id
            bet_obj_won = self.env['dpl.betting'].search([('bet_on', '=', participant)])
            i=0
            for amount in bet_obj_won:
                bet_by = self.env['dpl.betting'].search([('id', '=', bet_obj_won.ids[i])])
                participant_id = self.env['dpl.participants'].search([('id', '=', bet_by.name.id)]).id
                bal = amount.amount/20
                settlement_amount2 = amount.amount + (bal * amount_shared)
                self._cr.execute(" UPDATE dpl_participants SET balance_amount = balance_amount + %s WHERE id=%s",(settlement_amount2,participant_id,))
                self._cr.execute(" UPDATE dpl_betting SET amount_won =  %s WHERE id=%s",
                                 (settlement_amount2, bet_by.id,))
                i = i + 1

            if self.participant_1.id != vals['winner']:
                looser_id = self.participant_1.id
            else:
                looser_id = self.participant_2.id

            participant2 = self.env['dpl.participants'].search([('id', '=', looser_id)]).id
            bet_obj_won2 = self.env['dpl.betting'].search([('bet_on', '=', participant2),('match', '=', match_id)])
            i2 = 0
            for amount in bet_obj_won2:
                bet_by2 = self.env['dpl.betting'].search([('id', '=', bet_obj_won2.ids[i2])])
                participant_id = self.env['dpl.participants'].search([('id', '=', bet_by2.name.id)]).id
                bal2 = amount.amount
                bal2 = - bal2
                self._cr.execute("UPDATE dpl_participants SET balance_amount = balance_amount + %s WHERE id=%s",(bal2,participant_id,))
                self._cr.execute(" UPDATE dpl_betting SET amount_won =  %s WHERE id=%s",
                                 (bal2, bet_by2.id,))
                i2 = i2 + 1

        #  no bet on winner
        # if bet_obj_won.ids.__len__() != 0:
        #     if self.participant_1.id != vals['winner']:
        #         looser_id = self.participant_1.id
        #     else:
        #         looser_id = self.participant_2.id
        #
        #     participant2 = self.env['dpl.participants'].search([('id', '=', looser_id)]).id
        #     bet_obj_won2 = self.env['dpl.betting'].search([('bet_on', '=', participant2),('match', '=', match_id)])
        #     i2 = 0
        #     for amount in bet_obj_won2:
        #         bet_by2 = self.env['dpl.betting'].search([('id', '=', bet_obj_won2.ids[i2])])
        #         participant_id = self.env['dpl.participants'].search([('id', '=', bet_by2.name.id)]).id
        #         bal2 = amount.amount
        #         bal2 = - bal2
        #         self._cr.execute("UPDATE dpl_participants SET balance_amount = balance_amount + %s WHERE id=%s",(bal2,participant_id,))
        #         self._cr.execute(" UPDATE dpl_betting SET amount_won =  %s WHERE id=%s",
        #                          (bal2, bet_by2.id,))
        #         i2 = i2 + 1

        match = self.env['dpl.match'].search([('participant_1', '=', self.participant_1.id), ('participant_2', '=', self.participant_2.id)])

        if match.winner:
            raise exceptions.UserError(("Winner already set"))
        else:
            self._cr.execute("UPDATE dpl_match SET winner = %s WHERE id=%s",(vals['winner'], match_id,))
        return None

    def bet_on_total(self):
        participants = ['1', '2', '3']
        participants[0] = self.participant_2.id
        return {'domain': {'bet_amount': [('bet_on', '=', self.participant_2.id)]}}

    name = fields.Char(compute='match_name',store=False,string="Match")
    participant_1 = fields.Many2one('dpl.participants','Participant 1', required=True,store=True)
    participant_2 = fields.Many2one('dpl.participants','Participant 2', required=True,store=True)
    match_type = fields.Selection([('singles', 'Singles'),('doubles', 'Doubles')],string="Match type",required=True)
    winner = fields.Many2one('dpl.participants',string="Winner",change_default=True,store=True,
                             domain="['|',('id', '=', participant_1),('id', '=', participant_2)]")
    bet_amount = fields.One2many('dpl.betting','match', 'Betting',store=True)
    boolean = fields.Boolean('boolean', store=True,default=False)

    _sql_constraints = [
        ('name_uniq', 'unique(participant_1, participant_2)', 'Match already exists'),
    ]


class dpl_participants(models.Model):
    _name = 'dpl.participants'
    _description = 'dpl participants'

    name = fields.Char('Name')
    match_type = fields.Selection([('singles', 'Singles'), ('doubles', 'Doubles')], string="Match type", required=True)
    payement = fields.Integer('Payment')
    balance_amount = fields.Float('Balance',default=0)
    registered = fields.Boolean("Registered",default=False)

    _sql_constraints = [
        ('participant_uniq', 'unique (name)',
         _("Participant already exist!")),
    ]