from app.models.permissions import PermissionType, PermissionCategory

# Configuração padrão de permissões por role
DEFAULT_ROLE_PERMISSIONS = {
    "super_admin": [
        # Todas as permissões
        PermissionType.DASHBOARD_READ, PermissionType.DASHBOARD_WRITE,
        PermissionType.TRANSACTIONS_READ, PermissionType.TRANSACTIONS_WRITE, PermissionType.TRANSACTIONS_DELETE,
        PermissionType.ACCOUNTS_READ, PermissionType.ACCOUNTS_WRITE, PermissionType.ACCOUNTS_DELETE,
        PermissionType.GROUPS_READ, PermissionType.GROUPS_WRITE, PermissionType.GROUPS_DELETE,
        PermissionType.SUBGROUPS_READ, PermissionType.SUBGROUPS_WRITE, PermissionType.SUBGROUPS_DELETE,
        PermissionType.REPORTS_READ, PermissionType.REPORTS_EXPORT,
        PermissionType.FORECAST_READ, PermissionType.FORECAST_WRITE, PermissionType.FORECAST_DELETE,
        PermissionType.IMPORT_CSV,
        PermissionType.USERS_READ, PermissionType.USERS_WRITE, PermissionType.USERS_DELETE,
        PermissionType.PERMISSIONS_READ, PermissionType.PERMISSIONS_WRITE,
        PermissionType.COMPANIES_READ, PermissionType.COMPANIES_WRITE, PermissionType.COMPANIES_DELETE,
        PermissionType.BUSINESS_UNITS_READ, PermissionType.BUSINESS_UNITS_WRITE, PermissionType.BUSINESS_UNITS_DELETE,
        PermissionType.SETTINGS_READ, PermissionType.SETTINGS_WRITE
    ],
    "tenant_admin": [
        # Permissões de tenant (todas exceto super admin)
        PermissionType.DASHBOARD_READ, PermissionType.DASHBOARD_WRITE,
        PermissionType.TRANSACTIONS_READ, PermissionType.TRANSACTIONS_WRITE, PermissionType.TRANSACTIONS_DELETE,
        PermissionType.ACCOUNTS_READ, PermissionType.ACCOUNTS_WRITE, PermissionType.ACCOUNTS_DELETE,
        PermissionType.GROUPS_READ, PermissionType.GROUPS_WRITE, PermissionType.GROUPS_DELETE,
        PermissionType.SUBGROUPS_READ, PermissionType.SUBGROUPS_WRITE, PermissionType.SUBGROUPS_DELETE,
        PermissionType.REPORTS_READ, PermissionType.REPORTS_EXPORT,
        PermissionType.FORECAST_READ, PermissionType.FORECAST_WRITE, PermissionType.FORECAST_DELETE,
        PermissionType.IMPORT_CSV,
        PermissionType.USERS_READ, PermissionType.USERS_WRITE, PermissionType.USERS_DELETE,
        PermissionType.PERMISSIONS_READ, PermissionType.PERMISSIONS_WRITE,
        PermissionType.BUSINESS_UNITS_READ, PermissionType.BUSINESS_UNITS_WRITE, PermissionType.BUSINESS_UNITS_DELETE,
        PermissionType.SETTINGS_READ, PermissionType.SETTINGS_WRITE
    ],
    "business_unit_manager": [
        # Permissões de BU
        PermissionType.DASHBOARD_READ,
        PermissionType.TRANSACTIONS_READ, PermissionType.TRANSACTIONS_WRITE,
        PermissionType.ACCOUNTS_READ, PermissionType.ACCOUNTS_WRITE,
        PermissionType.GROUPS_READ, PermissionType.GROUPS_WRITE,
        PermissionType.SUBGROUPS_READ, PermissionType.SUBGROUPS_WRITE,
        PermissionType.REPORTS_READ, PermissionType.REPORTS_EXPORT,
        PermissionType.FORECAST_READ, PermissionType.FORECAST_WRITE,
        PermissionType.IMPORT_CSV,
        PermissionType.USERS_READ, PermissionType.USERS_WRITE,
        PermissionType.PERMISSIONS_READ, PermissionType.PERMISSIONS_WRITE
    ],
    "department_manager": [
        # Permissões de departamento
        PermissionType.DASHBOARD_READ,
        PermissionType.TRANSACTIONS_READ, PermissionType.TRANSACTIONS_WRITE,
        PermissionType.ACCOUNTS_READ,
        PermissionType.GROUPS_READ,
        PermissionType.SUBGROUPS_READ,
        PermissionType.REPORTS_READ,
        PermissionType.FORECAST_READ, PermissionType.FORECAST_WRITE
    ],
    "user": [
        # Permissões básicas
        PermissionType.DASHBOARD_READ,
        PermissionType.TRANSACTIONS_READ,
        PermissionType.ACCOUNTS_READ,
        PermissionType.GROUPS_READ,
        PermissionType.SUBGROUPS_READ,
        PermissionType.REPORTS_READ
    ]
}

# Mapeamento de permissões para categorias
PERMISSION_CATEGORIES = {
    PermissionType.DASHBOARD_READ: PermissionCategory.DASHBOARD,
    PermissionType.DASHBOARD_WRITE: PermissionCategory.DASHBOARD,
    
    PermissionType.TRANSACTIONS_READ: PermissionCategory.FINANCIAL,
    PermissionType.TRANSACTIONS_WRITE: PermissionCategory.FINANCIAL,
    PermissionType.TRANSACTIONS_DELETE: PermissionCategory.FINANCIAL,
    PermissionType.ACCOUNTS_READ: PermissionCategory.FINANCIAL,
    PermissionType.ACCOUNTS_WRITE: PermissionCategory.FINANCIAL,
    PermissionType.ACCOUNTS_DELETE: PermissionCategory.FINANCIAL,
    PermissionType.GROUPS_READ: PermissionCategory.FINANCIAL,
    PermissionType.GROUPS_WRITE: PermissionCategory.FINANCIAL,
    PermissionType.GROUPS_DELETE: PermissionCategory.FINANCIAL,
    PermissionType.SUBGROUPS_READ: PermissionCategory.FINANCIAL,
    PermissionType.SUBGROUPS_WRITE: PermissionCategory.FINANCIAL,
    PermissionType.SUBGROUPS_DELETE: PermissionCategory.FINANCIAL,
    PermissionType.FORECAST_READ: PermissionCategory.FINANCIAL,
    PermissionType.FORECAST_WRITE: PermissionCategory.FINANCIAL,
    PermissionType.FORECAST_DELETE: PermissionCategory.FINANCIAL,
    
    PermissionType.REPORTS_READ: PermissionCategory.REPORTS,
    PermissionType.REPORTS_EXPORT: PermissionCategory.REPORTS,
    
    PermissionType.USERS_READ: PermissionCategory.ADMINISTRATION,
    PermissionType.USERS_WRITE: PermissionCategory.ADMINISTRATION,
    PermissionType.USERS_DELETE: PermissionCategory.ADMINISTRATION,
    PermissionType.PERMISSIONS_READ: PermissionCategory.ADMINISTRATION,
    PermissionType.PERMISSIONS_WRITE: PermissionCategory.ADMINISTRATION,
    PermissionType.COMPANIES_READ: PermissionCategory.ADMINISTRATION,
    PermissionType.COMPANIES_WRITE: PermissionCategory.ADMINISTRATION,
    PermissionType.COMPANIES_DELETE: PermissionCategory.ADMINISTRATION,
    PermissionType.BUSINESS_UNITS_READ: PermissionCategory.ADMINISTRATION,
    PermissionType.BUSINESS_UNITS_WRITE: PermissionCategory.ADMINISTRATION,
    PermissionType.BUSINESS_UNITS_DELETE: PermissionCategory.ADMINISTRATION,
    
    PermissionType.IMPORT_CSV: PermissionCategory.SYSTEM,
    PermissionType.SETTINGS_READ: PermissionCategory.SYSTEM,
    PermissionType.SETTINGS_WRITE: PermissionCategory.SYSTEM
}

# Descrições das permissões
PERMISSION_DESCRIPTIONS = {
    PermissionType.DASHBOARD_READ: "Visualizar dashboard",
    PermissionType.DASHBOARD_WRITE: "Modificar dashboard",
    
    PermissionType.TRANSACTIONS_READ: "Visualizar transações",
    PermissionType.TRANSACTIONS_WRITE: "Criar e editar transações",
    PermissionType.TRANSACTIONS_DELETE: "Excluir transações",
    
    PermissionType.ACCOUNTS_READ: "Visualizar contas",
    PermissionType.ACCOUNTS_WRITE: "Criar e editar contas",
    PermissionType.ACCOUNTS_DELETE: "Excluir contas",
    
    PermissionType.GROUPS_READ: "Visualizar grupos de contas",
    PermissionType.GROUPS_WRITE: "Criar e editar grupos de contas",
    PermissionType.GROUPS_DELETE: "Excluir grupos de contas",
    
    PermissionType.SUBGROUPS_READ: "Visualizar subgrupos de contas",
    PermissionType.SUBGROUPS_WRITE: "Criar e editar subgrupos de contas",
    PermissionType.SUBGROUPS_DELETE: "Excluir subgrupos de contas",
    
    PermissionType.REPORTS_READ: "Visualizar relatórios",
    PermissionType.REPORTS_EXPORT: "Exportar relatórios",
    
    PermissionType.FORECAST_READ: "Visualizar previsões",
    PermissionType.FORECAST_WRITE: "Criar e editar previsões",
    PermissionType.FORECAST_DELETE: "Excluir previsões",
    
    PermissionType.IMPORT_CSV: "Importar dados via CSV",
    
    PermissionType.USERS_READ: "Visualizar usuários",
    PermissionType.USERS_WRITE: "Criar e editar usuários",
    PermissionType.USERS_DELETE: "Excluir usuários",
    
    PermissionType.PERMISSIONS_READ: "Visualizar permissões",
    PermissionType.PERMISSIONS_WRITE: "Gerenciar permissões",
    
    PermissionType.COMPANIES_READ: "Visualizar empresas",
    PermissionType.COMPANIES_WRITE: "Criar e editar empresas",
    PermissionType.COMPANIES_DELETE: "Excluir empresas",
    
    PermissionType.BUSINESS_UNITS_READ: "Visualizar unidades de negócio",
    PermissionType.BUSINESS_UNITS_WRITE: "Criar e editar unidades de negócio",
    PermissionType.BUSINESS_UNITS_DELETE: "Excluir unidades de negócio",
    
    PermissionType.SETTINGS_READ: "Visualizar configurações",
    PermissionType.SETTINGS_WRITE: "Modificar configurações"
}

# Mapeamento de funcionalidades para permissões
FUNCTIONALITY_PERMISSIONS = {
    "dashboard": [PermissionType.DASHBOARD_READ, PermissionType.DASHBOARD_WRITE],
    "transactions": [PermissionType.TRANSACTIONS_READ, PermissionType.TRANSACTIONS_WRITE, PermissionType.TRANSACTIONS_DELETE],
    "accounts": [PermissionType.ACCOUNTS_READ, PermissionType.ACCOUNTS_WRITE, PermissionType.ACCOUNTS_DELETE],
    "groups": [PermissionType.GROUPS_READ, PermissionType.GROUPS_WRITE, PermissionType.GROUPS_DELETE],
    "subgroups": [PermissionType.SUBGROUPS_READ, PermissionType.SUBGROUPS_WRITE, PermissionType.SUBGROUPS_DELETE],
    "reports": [PermissionType.REPORTS_READ, PermissionType.REPORTS_EXPORT],
    "forecast": [PermissionType.FORECAST_READ, PermissionType.FORECAST_WRITE, PermissionType.FORECAST_DELETE],
    "import": [PermissionType.IMPORT_CSV],
    "users": [PermissionType.USERS_READ, PermissionType.USERS_WRITE, PermissionType.USERS_DELETE],
    "permissions": [PermissionType.PERMISSIONS_READ, PermissionType.PERMISSIONS_WRITE],
    "companies": [PermissionType.COMPANIES_READ, PermissionType.COMPANIES_WRITE, PermissionType.COMPANIES_DELETE],
    "business_units": [PermissionType.BUSINESS_UNITS_READ, PermissionType.BUSINESS_UNITS_WRITE, PermissionType.BUSINESS_UNITS_DELETE],
    "settings": [PermissionType.SETTINGS_READ, PermissionType.SETTINGS_WRITE]
}
