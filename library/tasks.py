from collections import defaultdict
from celery import shared_task
from .models import Loan
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

@shared_task
def send_loan_notification(loan_id):
    try:
        loan = Loan.objects.get(id=loan_id)
        member_email = loan.member.user.email
        book_title = loan.book.title
        send_mail(
            subject='Book Loaned Successfully',
            message=f'Hello {loan.member.user.username},\n\nYou have successfully loaned "{book_title}".\nPlease return it by the due date.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member_email],
            fail_silently=False,
        )
    except Loan.DoesNotExist:
        pass


@shared_task(name='check_overdue_loans')
def check_overdue_loans():
    today = timezone.now().date()
    loans = Loan.objects.filter(is_returned=False, due_date=today).select_related('member__user', 'book')
    loan_by_member = defaultdict(list)
    
    for loan in loans:
        loan_by_member[loan.member] = loan
    
    for member, loans in loan_by_member.items():
        email = member.user.email
        book_titles = "\n".join([ loan.book.title for loan in loans])
        message = f"Hey \n Here is a list of over due books:\n {book_titles}"
        send_mail(
            subject='Overdue Book Notification',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )