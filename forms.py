from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, IntegerField, DateField, SelectField, TextAreaField, BooleanField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password')])

class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=100)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=200)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    buying_price = FloatField('Buying Price', validators=[DataRequired(), NumberRange(min=0)])
    selling_price = FloatField('Selling Price', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    expiry_date = DateField('Expiry Date', validators=[DataRequired()])
    tax_rate = FloatField('Tax Rate (%)', validators=[DataRequired(), NumberRange(min=0, max=100)], default=18.00)
    reorder_level = IntegerField('Reorder Level', validators=[Optional(), NumberRange(min=0)], default=5)
    sku = StringField('SKU', validators=[Optional(), Length(max=50)])
    barcode = StringField('Barcode', validators=[Optional(), Length(max=100)])

class BranchForm(FlaskForm):
    branch_code = StringField('Branch Code', validators=[DataRequired(), Length(max=20)])
    branch_name = StringField('Branch Name', validators=[DataRequired(), Length(max=100)])
    location = StringField('Location', validators=[DataRequired(), Length(max=255)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=100)])
    manager = StringField('Manager', validators=[DataRequired(), Length(max=100)])
    address = TextAreaField('Address', validators=[Optional()])
    tax_id = StringField('Tax ID', validators=[Optional(), Length(max=50)])
    is_active = BooleanField('Active')

class SupplierForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(), Length(max=200)])
    contact_person = StringField('Contact Person', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=100)])
    address = TextAreaField('Address', validators=[Optional()])
    tax_id = StringField('Tax ID', validators=[Optional(), Length(max=50)])
    payment_terms = StringField('Payment Terms', validators=[Optional(), Length(max=100)])
    lead_time_days = IntegerField('Lead Time (Days)', validators=[Optional(), NumberRange(min=1)], default=7)

class ExpenseForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Category', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    paid_to = StringField('Paid To', validators=[DataRequired(), Length(max=200)])
    receipt_number = StringField('Receipt Number', validators=[Optional(), Length(max=100)])

class CashSessionForm(FlaskForm):
    opening_balance = FloatField('Opening Balance', validators=[DataRequired(), NumberRange(min=0)])

class CloseSessionForm(FlaskForm):
    closing_balance = FloatField('Closing Balance', validators=[DataRequired(), NumberRange(min=0)])

class PurchaseOrderForm(FlaskForm):
    supplier_id = SelectField('Supplier', coerce=int, validators=[DataRequired()])
    branch_id = SelectField('Branch', coerce=int, validators=[DataRequired()])
    order_date = DateField('Order Date', validators=[DataRequired()])
    expected_date = DateField('Expected Delivery', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])

class StockTransferForm(FlaskForm):
    from_branch_id = SelectField('From Branch', coerce=int, validators=[DataRequired()])
    to_branch_id = SelectField('To Branch', coerce=int, validators=[DataRequired()])
    transfer_date = DateField('Transfer Date', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])

class CompanySettingsForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(), Length(max=200)])
    tagline = StringField('Tagline', validators=[Optional(), Length(max=200)])
    address = TextAreaField('Address', validators=[Optional()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=100)])
    website = StringField('Website', validators=[Optional(), Length(max=100)])
    tax_number = StringField('Tax Number', validators=[Optional(), Length(max=50)])
    footer_text = TextAreaField('Footer Text', validators=[Optional()])
    logo = FileField('Logo', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'svg'], 'Images only!')])
    favicon = FileField('Favicon', validators=[FileAllowed(['ico', 'png', 'svg'], 'Icon files only!')])

class DateRangeForm(FlaskForm):
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    branch_id = SelectField('Branch', coerce=int, validators=[Optional()])