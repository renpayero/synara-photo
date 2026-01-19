# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo import fields

class TestMilestonePayment(TransactionCase):

    def setUp(self):
        super(TestMilestonePayment, self).setUp()
        self.Project = self.env['project.project']
        self.Task = self.env['project.task']
        self.Milestone = self.env['project.milestone']
        self.User = self.env['res.users']
        
        self.user_implementer = self.User.create({
            'name': 'Implementer User',
            'login': 'implementer',
            'email': 'implementer@test.com',
        })
        
        self.project = self.Project.create({
            'name': 'Test Project',
            'allow_timesheets': True,
        })
        
        self.milestone = self.Milestone.create({
            'name': 'Test Milestone',
            'project_id': self.project.id,
            'user_id': self.user_implementer.id,
            'milestone_amount': 1000.0,
            'bonus_percentage': 10.0,
            'required_progress_percentage': 10.0,
            'planned_date_start': fields.Date.add(fields.Date.today(), days=5),
            'planned_date_end': fields.Date.add(fields.Date.today(), days=10),
        })

    def test_start_payment_eligibility(self):
        # Create a task linked to the milestone
        task = self.Task.create({
            'name': 'Task 1',
            'project_id': self.project.id,
            'milestone_id': self.milestone.id,
            'allocated_hours': 10.0,
        })
        
        # Initial state
        self.assertEqual(self.milestone.payment_status, 'draft')
        self.assertEqual(self.milestone.progress_percentage, 0.0)
        
        # Log 0.5 hours (5% progress) - Should not trigger payment
        task.write({'effective_hours': 0.5}) # Simulating timesheet entry
        # Trigger compute
        self.milestone._compute_hours_and_progress()
        self.assertEqual(self.milestone.progress_percentage, 5.0)
        self.assertEqual(self.milestone.payment_status, 'draft')
        
        # Log 1.0 hours total (10% progress) - Should trigger payment
        task.write({'effective_hours': 1.0})
        self.milestone._compute_hours_and_progress()
        self.assertEqual(self.milestone.progress_percentage, 10.0)
        self.assertEqual(self.milestone.payment_status, 'to_pay')

    def test_bonus_eligibility_success(self):
        # Create a task and complete it
        task = self.Task.create({
            'name': 'Task 1',
            'project_id': self.project.id,
            'milestone_id': self.milestone.id,
            'allocated_hours': 10.0,
            'state': '1_done', # Assuming '1_done' is the done state key
        })
        
        # Mark milestone as reached today (which is before planned_date_start)
        self.milestone.write({'is_reached': True})
        
        self.assertEqual(self.milestone.bonus_payment_status, 'to_pay')

    def test_bonus_eligibility_failure_late(self):
        # Set planned start date to yesterday
        self.milestone.planned_date_start = fields.Date.add(fields.Date.today(), days=-1)
        
        task = self.Task.create({
            'name': 'Task 1',
            'project_id': self.project.id,
            'milestone_id': self.milestone.id,
            'allocated_hours': 10.0,
            'state': '1_done',
        })
        
        # Mark milestone as reached today
        self.milestone.write({'is_reached': True})
        
        self.assertEqual(self.milestone.bonus_payment_status, 'not_eligible')

    def test_bonus_eligibility_failure_incomplete_tasks(self):
        task = self.Task.create({
            'name': 'Task 1',
            'project_id': self.project.id,
            'milestone_id': self.milestone.id,
            'allocated_hours': 10.0,
            'state': '01_in_progress', # Not done
        })
        
        # Try to mark milestone as reached
        with self.assertRaises(Exception): # Should raise ValidationError
            self.milestone.write({'is_reached': True})
