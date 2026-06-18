from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    household_name: Mapped[str] = mapped_column(String(160), nullable=False)
    marital_status: Mapped[str] = mapped_column(String(20), default="single", nullable=False)
    monthly_inflow: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    monthly_outflow: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    private_reserve_balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    private_reserve_target_override: Mapped[float | None] = mapped_column(Float, nullable=True)
    property_address: Mapped[str] = mapped_column(String(260), default="", nullable=False)
    property_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    people: Mapped[list["Person"]] = relationship(
        "Person", back_populates="client", cascade="all, delete-orphan", order_by="Person.role"
    )
    accounts: Mapped[list["Account"]] = relationship(
        "Account", back_populates="client", cascade="all, delete-orphan", order_by="Account.id"
    )
    liabilities: Mapped[list["Liability"]] = relationship(
        "Liability", back_populates="client", cascade="all, delete-orphan", order_by="Liability.id"
    )
    deductibles: Mapped[list["Deductible"]] = relationship(
        "Deductible", back_populates="client", cascade="all, delete-orphan", order_by="Deductible.id"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="client", cascade="all, delete-orphan", order_by="desc(Report.created_at)"
    )


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    ssn_last4: Mapped[str] = mapped_column(String(4), nullable=False)

    client: Mapped[Client] = relationship("Client", back_populates="people")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(24), nullable=False)
    account_type: Mapped[str] = mapped_column(String(80), nullable=False)
    institution: Mapped[str] = mapped_column(String(120), nullable=False)
    account_last4: Mapped[str] = mapped_column(String(4), default="", nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cash_balance: Mapped[float | None] = mapped_column(Float, nullable=True)

    client: Mapped[Client] = relationship("Client", back_populates="accounts")


class Liability(Base):
    __tablename__ = "liabilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    liability_type: Mapped[str] = mapped_column(String(80), nullable=False)
    lender: Mapped[str] = mapped_column(String(120), nullable=False)
    interest_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    client: Mapped[Client] = relationship("Client", back_populates="liabilities")


class Deductible(Base):
    __tablename__ = "deductibles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    client: Mapped[Client] = relationship("Client", back_populates="deductibles")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    quarter_label: Mapped[str] = mapped_column(String(40), nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    sacs_pdf_path: Mapped[str] = mapped_column(String(360), default="", nullable=False)
    tcc_pdf_path: Mapped[str] = mapped_column(String(360), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    client: Mapped[Client] = relationship("Client", back_populates="reports")
    snapshot: Mapped["ReportSnapshot"] = relationship(
        "ReportSnapshot", back_populates="report", cascade="all, delete-orphan", uselist=False
    )


class ReportSnapshot(Base):
    __tablename__ = "report_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False, unique=True, index=True)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    report: Mapped[Report] = relationship("Report", back_populates="snapshot")
