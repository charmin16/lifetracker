from turtle import title
from django.db.models import ExpressionWrapper, F, DecimalField, Case, Sum, When
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.utils.timezone import now
from .models import Expense, Idea, Requirement
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, TemplateView, DetailView, DeleteView, UpdateView
import json
from datetime import datetime, date, timedelta
from .forms import IdeaForm
import math

from django.contrib.auth.decorators import login_required


class Welcome(TemplateView):
    template_name = 'welcome.html'


class MainHome(TemplateView):
    template_name = 'main_home.html'


class Home(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


class CreateExpense(CreateView, LoginRequiredMixin):
    model = Expense
    fields = ['date', 'transaction_type', 'item_service', 'category', 'amount', 'note']
    template_name = 'create_expense.html'
    success_url = reverse_lazy('list-recent')

    def form_valid(self, form):
        form.instance.user = self.request.user  # attach logged-in user
        return super().form_valid(form)


class ListAllExpense(ListView, LoginRequiredMixin):
    model = Expense
    template_name = 'list_all.html'
    ordering = ['-date']
    # paginate_by = 8
    context_object_name = 'expenses'

    def get_queryset(self):
        qs = Expense.objects.filter(user=self.request.user).order_by('-date')

        month = self.request.GET.get("month")
        year = self.request.GET.get("year")
        days = self.request.GET.get("days")

        if month:  # example: "August 2025"
            try:
                parsed = datetime.strptime(month.strip(), "%B %Y")  # expects "August 2025"
                qs = qs.filter(date__year=parsed.year, date__month=parsed.month)
            except ValueError:
                pass  # ignore invalid input

        elif year:  # only year filter
            qs = qs.filter(date__year=year)

        elif days:  # last N days
            try:
                cutoff = now().date() - timedelta(days=int(days))
                qs = qs.filter(date__gte=cutoff)
            except ValueError:
                pass

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expenses = context['expenses']

        cash = 0
        balance = 0
        for expense in expenses:
            if expense.transaction_type == 'Credit':
                balance += expense.amount
            elif expense.transaction_type == 'Withdrawal':
                balance -= expense.amount
                cash += expense.amount
            elif expense.transaction_type == 'Transfer':
                balance -= expense.amount
            elif expense.transaction_type == 'Expense':
                if cash >= expense.amount:
                    cash -= expense.amount  # spend from cash
                else:
                    balance -= expense.amount  # spend directly from balance

            expense.bank_balance = balance
            expense.cash_balance = cash

        totals = (
            expenses.filter(user=self.request.user, transaction_type__in=['Expense', 'Transfer'])
            .exclude(category="")  # skip blank categories
            .values("category")
            .annotate(total_amount=Sum("amount"))
            .order_by("-total_amount")
        )

        # Build plain Python lists for Chart.js
        categories = [t["category"] for t in totals]
        amounts = [float(t["total_amount"]) for t in totals]  # make sure it's JSON-serializable

        context["totals"] = totals
        context["categories"] = json.dumps(categories)
        context["amounts"] = json.dumps(amounts)
        return context

    '''def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expenses = context['expenses']

        cash = 0
        balance = 0
        for expense in expenses:
            if expense.transaction_type == 'Credit':
                balance += expense.amount
            elif expense.transaction_type == 'Withdrawal':
                balance -= expense.amount
                cash += expense.amount
            elif expense.transaction_type == 'Transfer':
                balance -= expense.amount
            elif expense.transaction_type == 'Expense':
                cash -= expense.amount

            expense.bank_balance = balance
            expense.cash_balance = cash

        totals = (
            Expense.objects.filter(user=self.request.user).exclude(category__isnull=True)
            .values("category")
            .annotate(total_amount=Sum("amount"))
            .order_by("-total_amount")
        )

        context['totals'] = totals

        return context'''


class ListRecentExpense(ListView, LoginRequiredMixin):
    model = Expense
    template_name = 'list_recent.html'
    context_object_name = 'expenses'

    def get_queryset(self):
        # Show only the last 5 added (most recent insertions)
        return Expense.objects.filter(user=self.request.user).order_by('-id')[:5]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Don't calculate balances for recent view - it will be inaccurate
        # Instead, we'll modify the template to not show balance columns

        # For charts, we still want ALL data
        totals = (
            Expense.objects.filter(user=self.request.user, transaction_type__in=['Expense', 'Transfer'])
            .exclude(category="")
            .values("category")
            .annotate(total_amount=Sum("amount"))
            .order_by("-total_amount")
        )

        categories = [t["category"] for t in totals]
        amounts = [float(t["total_amount"]) for t in totals]

        context["totals"] = totals
        context["categories"] = json.dumps(categories)
        context["amounts"] = json.dumps(amounts)
        return context


@login_required
def create_idea(request):
    if request.method == "POST":
        form = IdeaForm(request.POST)
        if form.is_valid():
            idea = form.save(commit=False)
            idea.user = request.user
            idea.save()

            # Save requirements entered
            req_text = form.cleaned_data.get("requirements_text", "")
            if req_text:
                lines = [line.strip("-• ").strip() for line in req_text.splitlines() if line.strip()]
                for line in lines:
                    Requirement.objects.create(idea=idea, text=line)

            # ✅ force redirect so form clears and new idea shows
            return redirect("create_idea")
    else:
        form = IdeaForm()

    # Filtering logic
    ideas = Idea.objects.filter(user=request.user).order_by("-updated_at", "-created_at")

    category = request.GET.get("category")
    status = request.GET.get("status")
    priority = request.GET.get("priority")

    if category:
        ideas = ideas.filter(category=category)
    if status:
        ideas = ideas.filter(status=status)
    if priority:
        ideas = ideas.filter(priority=priority)

    # Progress circle calculation
    for idea in ideas:
        total_reqs = idea.requirements.count()
        done_reqs = idea.requirements.filter(is_done=True).count()
        idea.progress_pct = round(done_reqs * 100 / total_reqs) if total_reqs > 0 else 0
        idea.circle_offset = 188 - (idea.progress_pct * 188 / 100)

    context = {
        "form": form,
        "ideas": ideas,
        "selected_category": category,
        "selected_status": status,
        "selected_priority": priority,
    }
    return render(request, "ideas_2.html", context)


@login_required
def update_idea(request, pk):
    idea = get_object_or_404(Idea, pk=pk, user=request.user)

    if request.method == 'POST':
        form = IdeaForm(request.POST, instance=idea)
        if form.is_valid():
            idea = form.save()

            idea.last_updated = now()
            idea.save(update_fields=['updated_at'])

            # Save new requirements from textarea
            req_text = form.cleaned_data.get("requirements_text", "")
            if req_text:
                lines = [line.strip("-• ").strip() for line in req_text.splitlines() if line.strip()]
                for line in lines:
                    Requirement.objects.create(idea=idea, text=line)

            # Update checkboxes
            for req in idea.requirements.all():
                checked = request.POST.get(f"req_{req.id}") == "on"
                if req.is_done != checked:
                    req.is_done = checked
                    req.save()

            # Update status based on requirement completion
            idea.update_status()

            # ✅ FIX: Always redirect after successful update
            return redirect('create_idea')
        else:
            # Form is not valid - re-render with errors
            print("FORM ERRORS:", form.errors)
            return render(request, 'update_idea.html', {'form': form, 'idea': idea})
    else:
        form = IdeaForm(instance=idea)

    return render(request, 'update_idea.html', {'form': form, 'idea': idea})


class DeleteIdea(DeleteView):
    model = Idea
    template_name = 'delete.html'
    success_url = reverse_lazy('create_idea')


'''@login_required
def mark_done(request, idea_id):
    """Mark all requirements for a dream as done (progress 100%)."""
    idea = get_object_or_404(Idea, id=idea_id, user=request.user)

    # mark all requirements as done
    idea.requirements.update(is_done=True)

    # set status to "Done"
    idea.status = "Done"
    idea.save(update_fields=["status"])

    # optional: if you store progress in the model, enforce 100%
    if hasattr(idea, "progress_pct"):
        idea.progress_pct = 100
        idea.circle_offset = 0  # fully filled
        # only needed if you persist progress fields in DB

    return redirect("create_idea")
'''


@login_required
def mark_done(request, idea_id):
    idea = get_object_or_404(Idea, id=idea_id, user=request.user)

    if request.method == "POST":
        # mark all requirements as done
        idea.requirements.update(is_done=True)
        # ✅ recalc status automatically (will set to "Done")
        idea.update_status()

    return redirect("create_idea")

