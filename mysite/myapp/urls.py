from django.urls import path
from . import views
from django.contrib.auth import views as auth_user

urlpatterns = [
    path('', views.Welcome.as_view(), name='welcome'),
    path('login/', auth_user.LoginView.as_view(template_name='login.html'), name='login'),
    path('main-home/', views.MainHome.as_view(), name='main_home_page'),
    path('expense-home/', views.Home.as_view(), name='expense_home'),
    path('signup', views.signup, name='signup'),
    path('logout/', auth_user.LogoutView.as_view(), name='logout'),
    path('create-expense/', views.CreateExpense.as_view(), name='create-expense'),
    path('list-recent-records/', views.ListRecentExpense.as_view(), name='list-recent'),
    path('list-expense/', views.ListAllExpense.as_view(), name='list-expenses'),
    path('create-idea/', views.create_idea, name='create_idea'),
    path('delete-idea/<int:pk>', views.DeleteIdea.as_view(), name='delete_idea'),
    path('update_idea/<int:pk>', views.update_idea, name='update_idea'),
    path('mark-done/<int:idea_id>', views.mark_done, name='mark_done'),
    path('emergency-admin/', views.create_admin_view, name='emergency_admin')
]
